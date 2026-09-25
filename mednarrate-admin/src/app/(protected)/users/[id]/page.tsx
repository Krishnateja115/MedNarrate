import ClientPage from "./ClientPage";

export function generateStaticParams() {
  return [{ id: "1" }]; // Mock param for static build
}

export default function Page({ params }: { params: any }) {
  return <ClientPage params={params} />;
}
