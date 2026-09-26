

export default function StatCard({
    title,
    value,
  }: {
    title: string;
    value: number;
  }) {
    return (
      <div className="rounded-xl border bg-white p-5 shadow-sm">
        <p className="text-sm text-gray-500">{title}</p>
  
        <p className="mt-2 text-3xl font-bold">
          {value}
        </p>
      </div>
    );
  }