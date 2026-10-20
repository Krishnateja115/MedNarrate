# MedNarrate: deploy to one server (backend + admin portal) and release the Android app

Platform: **one DigitalOcean Droplet** (Ubuntu 24.04, Bangalore region) running the repo's Docker Compose
stack, with **Caddy** in front for free automatic HTTPS. Any Ubuntu server works the same way
(AWS Lightsail, Hetzner, a Google Cloud VM). Cloud Run is described in `mednarrate-backend/DEPLOYMENT.md`
and needs more services; this single-server route is the shortest correct path.

What runs on the server (all in Docker):
API, report worker, PostgreSQL (pgvector), Redis, admin portal, Caddy (HTTPS).
Only ports 22, 80, 443 are public. The database and Redis are not reachable from the internet.

Rough cost (check current prices): server about US$24/month for 4 GB RAM / 2 vCPU, domain about
US$1 to 12/year. Groq/Gemini free tiers have request limits.

> Do not put real patient data on it until backups, privacy terms and the privacy policy in the app
> are finished (see RELEASE_READINESS.md).

---------------------------------------------------------------------------------------------------

## Part 1: Accounts and names (about 20 minutes)

1. Create a DigitalOcean account (digitalocean.com) and add a payment method.
2. Pick two web addresses, one for the API and one for the admin portal:
   - With a domain you own, e.g. `api.yourdomain.com` and `admin.yourdomain.com`; or
   - Free: duckdns.org, create two names, e.g. `mednarrate-api.duckdns.org` and
     `mednarrate-admin.duckdns.org`.
3. On your Mac, create an SSH key if you do not have one:
   ```bash
   ssh-keygen -t ed25519 -C "mednarrate"
   cat ~/.ssh/id_ed25519.pub
   ```
   Copy the printed line (starts with `ssh-ed25519`).

## Part 2: Create the server

1. DigitalOcean, Create, Droplets.
2. Region: **Bangalore (BLR1)**. Image: **Ubuntu 24.04 LTS**.
3. Size: Basic, Regular, **4 GB RAM / 2 vCPU**. Do not choose 1 or 2 GB (the AI models need memory).
4. Authentication: SSH key, add the line you copied. Hostname: `mednarrate`. Create.
5. Note the server's public IP address, e.g. `203.0.113.10`.

## Part 3: Point your addresses at the server

At your domain provider (or in DuckDNS) create two **A records** pointing at the server IP:

| Name  | Type | Value         |
|-------|------|---------------|
| api   | A    | 203.0.113.10  |
| admin | A    | 203.0.113.10  |

Check from your Mac (repeat for the admin name); it must print the server IP before you go on:
```bash
dig +short api.yourdomain.com
```

## Part 4: Prepare the server (once)

```bash
ssh root@203.0.113.10
apt update && apt -y upgrade
curl -fsSL https://get.docker.com | sh
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
docker --version && docker compose version
exit
```

## Part 5: Send the code to the server

On your Mac, in the repository root (`MedNarrate-main`):
```bash
bash deploy/make_bundle.sh
scp mednarrate-server.tar.gz root@203.0.113.10:/root/
```
The bundle contains no secrets, databases or uploads. Then on the server:
```bash
ssh root@203.0.113.10
mkdir -p /root/mednarrate && tar -xzf mednarrate-server.tar.gz -C /root/mednarrate
cd /root/mednarrate
```

## Part 6: Settings and secrets (on the server)

```bash
cp .env.deploy.example .env
echo "POSTGRES_PASSWORD: $(openssl rand -hex 24)"
echo "JWT_SECRET: $(openssl rand -hex 32)"
echo "ENCRYPTION_KEY: $(openssl rand -base64 32 | tr '+/' '-_')"
nano .env
```
In `.env` fill in:
- `API_DOMAIN`, `ADMIN_DOMAIN`, `TEAM_DOMAIN` (your three addresses, without `https://`; TEAM_DOMAIN serves the static team website from the `website/` folder)
- `POSTGRES_PASSWORD`, `JWT_SECRET`, `ENCRYPTION_KEY` (the three values printed above)
- `CORS_ORIGINS=["https://admin.yourdomain.com"]` and `ADMIN_APP_ORIGIN=https://admin.yourdomain.com`
- `GROQ_API_KEY` (and `GEMINI_API_KEY` / others if you use them)

Save: Ctrl+O, Enter, Ctrl+X. Keep a private copy of `ENCRYPTION_KEY` and `JWT_SECRET`
(a password manager). Do not paste the `.env` anywhere public, and use new keys, not ones from
your laptop `.env`.

## Part 7: Start everything

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f backend
```
- The first build takes about 10 to 20 minutes. The first start downloads the NER model.
- The database migrations run automatically.
- Press Ctrl+C to stop watching the log (the services keep running).
- When `docker compose ps` shows backend `healthy`, check from your Mac:
  ```bash
  curl https://api.yourdomain.com/health
  ```
  Then open `https://admin.yourdomain.com` (the certificate is issued on first visit, wait a minute
  if the browser complains).

## Part 8: First admin account, AI settings, flags

```bash
docker compose exec -e ADMIN_EMAIL=you@example.com backend python scripts/create_admin.py
docker compose exec backend python scripts/build_knowledge_base.py
```
(the first prompts for a password of at least 14 characters; the second builds the general
medical knowledge the chat uses.)

Then in the admin portal (`https://admin.yourdomain.com`):
1. Log in. If the account asks for it, finish MFA setup.
2. **AI Configuration**: set Groq as primary, add a fallback, save.
3. **Feature Flags**: create `report_type_check`, turn it ON, rollout 100.
   Leave `rag_hallucination_guard` and `experimental_medical_verifier` OFF.
4. **Models & XAI** should show the MRAD dataset card.

## Part 9: Build the Android app for the server

1. Create a release keystore once (keep it safe and backed up; losing it means you can never update
   the same app on Google Play):
   ```bash
   keytool -genkey -v -keystore ~/mednarrate-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias release
   ```
2. Copy `android/key.properties.example` to `android/key.properties` and fill in the passwords and
   `storeFile=/Users/<you>/mednarrate-release.jks`. It is in `.gitignore`; never commit it.
3. Build:
   ```bash
   flutter clean && flutter pub get
   flutter build apk --release \
     --dart-define=API_BASE_URL=https://api.yourdomain.com \
     --dart-define=ENVIRONMENT=production
   ```
   Output: `build/app/outputs/flutter-apk/app-release.apk`.
4. Install on your phone to test: `adb install -r build/app/outputs/flutter-apk/app-release.apk`
   (or send the file to the phone). Test: sign up, upload a lab report, chat, translate, offline.
5. Sharing: send the APK directly (testers must allow "install unknown apps").
   For Google Play use `flutter build appbundle --release ...` with the same defines; Play needs a
   one-time US$25 developer account, a privacy-policy URL, and a review. iOS needs an Apple Developer
   account (US$99/year) and Xcode signing; not covered here.

## Part 10: Acceptance test on the live system

- `/health` returns OK over HTTPS; the admin portal logs in.
- Sign up in the app, upload a real lab report: it finishes. Upload an unrelated document (invoice):
  it is rejected.
- Chat answers, translation works, the "Looks like a blood-test report" chip shows (flag on).
- Restart the worker mid-report (`docker compose restart worker`): the report still completes.
- Speed: `docker compose exec backend python scripts/timing_report.py`.

## Part 11: Updating later

On the Mac: `bash deploy/make_bundle.sh && scp mednarrate-server.tar.gz root@IP:/root/`
On the server:
```bash
cd /root/mednarrate && tar -xzf ../mednarrate-server.tar.gz -C . && docker compose up -d --build
```
Your `.env` and all data are kept (the bundle never contains them). Migrations run on start.
If the code changed the Flutter app, rebuild and reinstall the APK.

## Part 12: Backups and care

- Daily database dump (run once to test, then put it in `crontab -e`):
  ```bash
  cd /root/mednarrate && docker compose exec -T db pg_dump -U mednarrate_user mednarrate | gzip > /root/backup-$(date +%F).sql.gz
  ```
  Copy dumps off the server regularly; consider the Droplet "Backups" option too.
- Uploaded report files live in the Docker volume `uploads`; they are not in the dump.
- Watch disk space: `df -h`. Logs: `docker compose logs --tail=100 backend`.
- Security: SSH keys only, firewall as above, never open port 5432 or 6379, rotate any key that was
  ever pasted into chat.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Browser warns about the certificate | The DNS records are not live yet, or ports 80/443 are blocked. Wait, check `dig`, check `ufw status`. |
| `backend` keeps restarting, log says "JWT_SECRET must be configured" | Regenerate `JWT_SECRET` with `openssl rand -hex 32`. |
| Log says "Wildcard CORS" or "CORS_ORIGINS" | `CORS_ORIGINS` must be a JSON list, e.g. `["https://admin.yourdomain.com"]`. |
| Reports stay "processing" | The `worker` container is down: `docker compose ps`, `docker compose logs worker`. |
| Admin login fails or loops | `ADMIN_APP_ORIGIN` / `CORS_ORIGINS` must match the admin address exactly (https, no trailing slash). |
| App says it cannot connect | The APK was built with the wrong `API_BASE_URL`; rebuild with the https address. |
| Out of memory during build | Check the swap (`free -h`) or use the 8 GB size for the first build, then resize back. |
