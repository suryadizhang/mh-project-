import { NextRequest, NextResponse } from 'next/server'
import { writeFile, readFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

const COMPANY_SETTINGS_FILE = path.join(process.cwd(), 'data', 'company-settings.json')

interface CompanySettings {
  baseFeeStructure: {
    freeRadius: number
    ratePerMile: number
  }
  serviceArea: {
    description: string
    maxRadius: number
  }
  contactInfo: {
    phone: string
    email: string
  }
  lastUpdated: string
  updatedBy: string
}

// Default company settings
const DEFAULT_SETTINGS: CompanySettings = {
  baseFeeStructure: {
    freeRadius: 30,
    ratePerMile: 2
  },
  serviceArea: {
    description: 'Northern California',
    maxRadius: 150
  },
  contactInfo: {
    phone: '(916) 740-8768',
    email: 'cs@myhibachichef.com'
  },
  lastUpdated: '2025-01-15',
  updatedBy: 'System Default'
}

async function getCompanySettings(): Promise<CompanySettings> {
  try {
    if (existsSync(COMPANY_SETTINGS_FILE)) {
      const data = await readFile(COMPANY_SETTINGS_FILE, 'utf8')
      return JSON.parse(data)
    }
  } catch (error) {
    console.error('Error reading company settings file:', error)
  }
  
  // Return default if file doesn't exist or has errors
  return DEFAULT_SETTINGS
}

async function saveCompanySettings(settings: CompanySettings): Promise<void> {
  try {
    // Ensure data directory exists
    const dataDir = path.dirname(COMPANY_SETTINGS_FILE)
    if (!existsSync(dataDir)) {
      await writeFile(dataDir, '', { flag: 'wx' }).catch(() => {}) // Create directory
    }
    
    await writeFile(COMPANY_SETTINGS_FILE, JSON.stringify(settings, null, 2))
  } catch (error) {
    console.error('Error saving company settings file:', error)
    throw new Error('Failed to save company settings')
  }
}

// GET: Retrieve current company settings
export async function GET() {
  try {
    const settings = await getCompanySettings()
    return NextResponse.json(settings)
  } catch (error) {
    console.error('Error fetching company settings:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// PUT: Update company settings
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Validate required fields
    if (!body.baseFeeStructure || !body.serviceArea || !body.contactInfo) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    // Validate numeric fields
    if (typeof body.baseFeeStructure.freeRadius !== 'number' || body.baseFeeStructure.freeRadius < 0) {
      return NextResponse.json(
        { error: 'Free radius must be a non-negative number' },
        { status: 400 }
      )
    }

    if (typeof body.baseFeeStructure.ratePerMile !== 'number' || body.baseFeeStructure.ratePerMile < 0) {
      return NextResponse.json(
        { error: 'Rate per mile must be a non-negative number' },
        { status: 400 }
      )
    }

    // Create updated settings
    const updatedSettings: CompanySettings = {
      baseFeeStructure: {
        freeRadius: body.baseFeeStructure.freeRadius,
        ratePerMile: body.baseFeeStructure.ratePerMile
      },
      serviceArea: {
        description: body.serviceArea.description || 'Northern California',
        maxRadius: body.serviceArea.maxRadius || 150
      },
      contactInfo: {
        phone: body.contactInfo.phone || '(916) 740-8768',
        email: body.contactInfo.email || 'cs@myhibachichef.com'
      },
      lastUpdated: body.lastUpdated || new Date().toISOString().split('T')[0],
      updatedBy: body.updatedBy || 'Admin'
    }

    // Save to file
    await saveCompanySettings(updatedSettings)
    
    return NextResponse.json(updatedSettings)
  } catch (error) {
    console.error('Error updating company settings:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
