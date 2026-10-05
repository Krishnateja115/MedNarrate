"""Focused translation tests; HTTP/model responses are synthetic fixtures."""
import json
import importlib.util
import sys
import types
import unittest
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI

from app.core.config import settings
from app.exceptions import TranslationServiceError, setup_exception_handlers
from app.services import llm_client


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_translation_payload_and_complete_multipart_response(self):
        original_client = httpx.AsyncClient
        def respond(request):
            self.assertNotIn('key=', str(request.url))
            self.assertEqual(request.headers['x-goog-api-key'], 'test-key')
            config = json.loads(request.content)['generationConfig']
            self.assertEqual(config['responseMimeType'], 'application/json')
            self.assertEqual(config['maxOutputTokens'], settings.TRANSLATION_MAX_OUTPUT_TOKENS)
            return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
                {'text': 'private thought', 'thought': True}, {'text': '{"value":'}, {'text': '"తెలుగు"}'},
            ]}}]})
        with patch.object(settings, 'GEMINI_API_KEY', 'test-key'), patch.object(settings, 'ENVIRONMENT', 'test'), patch.object(
            httpx, 'AsyncClient', side_effect=lambda **kw: original_client(transport=httpx.MockTransport(respond), **kw)
        ):
            token = llm_client._translation_request.set(True)
            try:
                response = await llm_client.DevGeminiProvider().generate('translate synthetic report')
                self.assertEqual(json.loads(response['content']), {'value': 'తెలుగు'})
            finally:
                llm_client._translation_request.reset(token)

    async def test_truncated_response_is_not_accepted(self):
        client = httpx.AsyncClient
        def respond(request):
            return httpx.Response(200, json={'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': [{'text': '{}'}]}}]})
        with patch.object(settings, 'GEMINI_API_KEY', 'test-key'), patch.object(settings, 'ENVIRONMENT', 'test'), patch.object(
            httpx, 'AsyncClient', side_effect=lambda **kw: client(transport=httpx.MockTransport(respond), **kw)
        ), patch('asyncio.sleep', new_callable=AsyncMock):
            with self.assertRaises(llm_client.LLMConnectionError):
                await llm_client.DevGeminiProvider().generate('translate synthetic report')

    async def test_failure_is_sanitized_and_request_options_reset(self):
        with patch.object(llm_client, 'generate_with_metadata', new=AsyncMock(side_effect=RuntimeError('secret upstream detail'))):
            with self.assertRaises(TranslationServiceError) as error:
                await llm_client.generate_translation('synthetic report')
        self.assertNotIn('secret', str(error.exception))
        self.assertFalse(llm_client._translation_request.get())

    async def test_rate_limit_is_not_immediately_retried(self):
        client = httpx.AsyncClient
        requests = []
        def respond(request):
            requests.append(request)
            return httpx.Response(429, json={'error': {'message': 'sensitive upstream text'}})
        with patch.object(settings, 'GEMINI_API_KEY', 'test-key'), patch.object(settings, 'ENVIRONMENT', 'test'), patch.object(
            httpx, 'AsyncClient', side_effect=lambda **kw: client(transport=httpx.MockTransport(respond), **kw)
        ):
            with self.assertRaises(ValueError) as error:
                await llm_client.DevGeminiProvider().generate('synthetic')
        self.assertEqual(len(requests), 1)
        self.assertNotIn('sensitive', str(error.exception))


class RouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # OCR/report generation is outside this endpoint test; no model downloads.
        pipeline = types.ModuleType('app.services.analysis_pipeline')
        pipeline.run_analysis = AsyncMock()
        key = 'app.services.analysis_pipeline'
        previous = sys.modules.get(key)
        sys.modules[key] = pipeline
        try:
            spec = importlib.util.spec_from_file_location(
                'translation_route_under_test', Path(__file__).parents[1] / 'app/api/v1/analysis.py')
            analysis = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(analysis)
        finally:
            if previous is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = previous
        self.route = analysis
        self.app = FastAPI()
        self.app.include_router(analysis.router, prefix='/reports')
        setup_exception_handlers(self.app)
        self.report_id = uuid.uuid4()
        self.user = types.SimpleNamespace(id=uuid.uuid4())
        self.source = types.SimpleNamespace(id=uuid.uuid4(), report_id=self.report_id,
            patient_summary='Hemoglobin 10.2 g/dL', clinician_summary='Clinician Summary text', abnormal_findings_source='abnormal findings', meds_list='meds list', abnormal_findings=[], structured_lab_values=[], doctor_discussion_points=['English text point'])
        self.saved = []
        self.db = types.SimpleNamespace(execute=AsyncMock(), commit=AsyncMock(), refresh=AsyncMock(),
            delete=AsyncMock(), flush=AsyncMock(), add=self.saved.append)
        self.db.execute.side_effect = [
            self.result(first=None), self.result(first=self.source), self.result(all=[]), self.result(first=None),
        ]
        self.app.dependency_overrides[analysis.get_current_user] = lambda: self.user
        self.app.dependency_overrides[analysis.get_db] = lambda: self.db
        self.ownership = patch.object(analysis, 'verify_report_ownership', new=AsyncMock(return_value=types.SimpleNamespace(id=self.report_id)))
        self.ownership.start()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='http://test')

    @staticmethod
    def result(first=None, all=None):
        return types.SimpleNamespace(
            scalars=lambda: types.SimpleNamespace(first=lambda: first, all=lambda: all),
            scalar_one_or_none=lambda: first
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        self.ownership.stop()

    def payload(self):
        text = 'మీ రక్త పరీక్ష నివేదిక'
        long_text = text + ' ' + text + ' ' + text
        return {'patient_summary': long_text + ' Hemoglobin 10.2 g/dL', 'clinician_summary': long_text, 'abnormal_findings': [],
            'medications': [], 'doctor_discussion_points': [text],
            'ui_labels': {key: text for key in self.route.REQUIRED_UI_LABEL_KEYS}}

    async def test_post_passes_language_and_stored_body_returns_unicode(self):
        with patch.object(self.route, 'generate_translation_with_provider', new=AsyncMock(return_value={
            'provider': 'dev_gemini', 'content': json.dumps(self.payload(), ensure_ascii=False)
        })) as model:
            response = await self.client.post(f'/reports/{self.report_id}/analysis/translate', json={'language': 'te'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['language'], 'te')
        self.assertIn('మీ రక్త', response.json()['patient_summary'])
        self.assertIn('Telugu', model.call_args.args[0])
        self.assertIn(self.source.patient_summary, model.call_args.args[0])
        self.assertEqual(self.saved[0].patient_summary, response.json()['patient_summary'])
        self.db.commit.assert_awaited_once()

    async def test_invalid_model_output_is_502_and_not_saved(self):
        with patch.object(self.route, 'generate_translation_with_provider', new=AsyncMock(return_value={'provider':'dev_gemini','content':'{}'})):
            response = await self.client.post(f'/reports/{self.report_id}/analysis/translate', json={'language':'te'})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['code'], 'translation_service_unavailable')
        self.assertEqual(self.saved, [])
        self.db.commit.assert_not_awaited()

    async def test_english_does_not_call_model(self):
        with patch.object(self.route, 'generate_translation_with_provider', new_callable=AsyncMock) as model:
            response = await self.client.post(f'/reports/{self.report_id}/analysis/translate', json={'language':'en'})
        self.assertEqual(response.json()['patient_summary'], self.source.patient_summary)
        model.assert_not_awaited()

    async def test_unsupported_language_is_rejected(self):
        response = await self.client.post(f'/reports/{self.report_id}/analysis/translate', json={'language':'invalid'})
        self.assertEqual(response.status_code, 400)

    async def test_failed_regeneration_preserves_existing_cache(self):
        stale = types.SimpleNamespace(schema_version=1, ui_labels={})
        self.db.execute.side_effect = [self.result(first=None), self.result(first=self.source), self.result(all=[]), self.result(first=stale)]
        with patch.object(self.route, 'generate_translation_with_provider', new=AsyncMock(side_effect=TranslationServiceError())):
            response = await self.client.post(f'/reports/{self.report_id}/analysis/translate', json={'language':'te'})
        self.assertEqual(response.status_code, 502)
        self.db.delete.assert_not_awaited()
        self.db.commit.assert_not_awaited()


if __name__ == '__main__':
    unittest.main()
