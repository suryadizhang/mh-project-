import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, email, subject, message, rating, category } = body;

    console.log('Feedback received:', { name, email, subject, message, category, rating });

    return NextResponse.json(
      { 
        success: true, 
        message: 'Thank you for your feedback! We appreciate your input.',
        id: Date.now().toString()
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Feedback submission error:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to submit feedback' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const category = searchParams.get('category');
    const page = searchParams.get('page') || '1';
    const limit = searchParams.get('limit') || '10';

    return NextResponse.json(
      { 
        success: true, 
        data: [],
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total: 0
        },
        category
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Feedback retrieval error:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to retrieve feedback' },
      { status: 500 }
    );
  }
}
