import { NextResponse } from 'next/server';

const base = process.env.BACKEND_INTERNAL_URL ?? 'http://127.0.0.1:8810';

export async function GET() {
  try {
    const res = await fetch(`${base}/health`, { cache: 'no-store' });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 502 });
  }
}
