export default async function CohortPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Cohort {id}</h1>
      <p>List of submissions for this cohort will go here.</p>
    </div>
  );
}
