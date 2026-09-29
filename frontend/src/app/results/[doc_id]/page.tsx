export default async function ResultPage({ params }: { params: Promise<{ doc_id: string }> }) {
  const { doc_id } = await params;
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Result for {doc_id}</h1>
      <p>PDF viewer and scoring results will go here.</p>
    </div>
  );
}
