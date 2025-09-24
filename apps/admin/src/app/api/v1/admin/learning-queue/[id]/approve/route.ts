import { NextRequest, NextResponse } from 'next/server';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  // This endpoint has been moved to the backend
  return NextResponse.json(
    {
      success: false,
      error: 'Endpoint moved',
      movedTo: `${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/learning-queue/${id}/approve`,
      message:
        'This admin endpoint has been moved to the backend for security reasons',
    },
    { status: 410 }
  );
}
