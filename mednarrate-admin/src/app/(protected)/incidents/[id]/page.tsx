import ClientPage from "./ClientPage";

export function generateStaticParams() {
  return [{ id: "1" }]; // Mock param for static build
}

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <ClientPage params={params} />;
}
