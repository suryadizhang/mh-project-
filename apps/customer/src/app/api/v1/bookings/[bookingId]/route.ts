import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ bookingId: string }> },
) {
  const { bookingId } = await context.params;

  return NextResponse.json({
    message: 'Booking details endpoint',
    bookingId,
    timestamp: new Date().toISOString(),
  });
}
