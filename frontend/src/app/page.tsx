import Link from "next/link";

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <p>List of rubrics and active cohorts will go here.</p>
      <Link href="/rubrics/new" className="text-blue-600 hover:underline mt-4 inline-block">Create New Rubric</Link>
    </div>
  );
}
