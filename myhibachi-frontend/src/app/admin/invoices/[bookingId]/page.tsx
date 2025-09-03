'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import {
  Download,
  Eye,
  DollarSign,
  FileText,
  Calculator,
  CreditCard,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

interface BookingData {
  bookingId: string
  confirmationNumber: string
  customerName: string
  customerEmail: string
  eventDate: string
  eventTime: string
  guestCount: number
  venueAddress: {
    street: string
    city: string
    state: string
    zipcode: string
  }
  services: Array<{
    name: string
    description: string
    price: number
    quantity: number
    category: string
  }>
  subtotal: number
  tax: number
  totalAmount: number
  appliedDiscounts?: Array<{
    name: string
    type: 'percentage' | 'fixed_amount'
    value: number
    amount: number
  }>
  paymentStatus: 'paid' | 'pending' | 'overdue'
  notes?: string
}

interface InvoiceSettings {
  depositAmount: number
  depositPaid: boolean
  additionalNotes: string
  paymentTerms: string
  travelMiles: number
  discountAmount: number
  discountDescription: string
}

export default function AdminInvoicePage() {
  const params = useParams()
  const bookingId = params?.bookingId as string

  const [booking, setBooking] = useState<BookingData | null>(null)
  const [invoiceSettings, setInvoiceSettings] = useState<InvoiceSettings>({
    depositAmount: 0,
    depositPaid: false,
    additionalNotes: '',
    paymentTerms: 'Due upon service completion',
    travelMiles: 0,
    discountAmount: 0,
    discountDescription: ''
  })
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  // Mock booking data - in production this would fetch from your API
  useEffect(() => {
    const fetchBooking = async () => {
      setLoading(true)
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))

        const mockBooking: BookingData = {
          bookingId: bookingId,
          confirmationNumber: `MH${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
          customerName: 'Sarah Johnson',
          customerEmail: 'sarah.johnson@email.com',
          eventDate: '2025-08-15',
          eventTime: '6:00 PM',
          guestCount: 8,
          venueAddress: {
            street: '123 Oak Street',
            city: 'San Jose',
            state: 'CA',
            zipcode: '95123'
          },
          services: [
            {
              name: 'Adult Hibachi Experience',
              description: 'Full hibachi dining experience with chef performance',
              price: 55,
              quantity: 6,
              category: 'hibachi_experience'
            },
            {
              name: 'Child Hibachi Experience (12 & Under)',
              description: 'Kids hibachi meal with smaller portions',
              price: 30,
              quantity: 2,
              category: 'hibachi_experience'
            },
            {
              name: 'Premium Steak Upgrade',
              description: 'Upgrade to premium filet mignon',
              price: 15,
              quantity: 2,
              category: 'add_ons'
            },
            {
              name: 'Lobster Tail Addition',
              description: 'Fresh lobster tail grilled hibachi style',
              price: 12,
              quantity: 4,
              category: 'add_ons'
            }
            // Travel fee is handled separately via distance calculation, not as a service
          ],
          subtotal: 468, // Updated to match actual services total
          tax: 0, // Tax will be calculated on final total including travel fees
          totalAmount: 468, // Will be recalculated with travel fees and tax
          appliedDiscounts: [
            // No automatic discounts - only admin-applied discounts
          ],
          paymentStatus: 'pending',
          notes: 'Customer requested extra ginger sauce'
        }

        setBooking(mockBooking)
      } catch (error) {
        console.error('Error fetching booking:', error)
      } finally {
        setLoading(false)
      }
    }

    if (bookingId) {
      fetchBooking()
    }
  }, [bookingId])

  const calculateTravelFee = () => {
    return invoiceSettings.travelMiles * 2 // $2 per mile
  }

  const calculateTax = () => {
    if (!booking) return 0

    // Calculate services subtotal (without automatic discounts)
    const servicesSubtotal = booking.services.reduce(
      (sum, service) => sum + service.price * service.quantity,
      0
    )

    // Add travel fee and apply admin discount
    const travelFee = calculateTravelFee()
    const subtotalWithTravel = servicesSubtotal + travelFee
    const subtotalAfterDiscount = subtotalWithTravel - invoiceSettings.discountAmount

    // Calculate 8% tax on the subtotal
    return Math.max(subtotalAfterDiscount, 0) * 0.08
  }

  const calculateTotalWithAdjustments = () => {
    if (!booking) return 0

    // Calculate services subtotal (without automatic discounts)
    const servicesSubtotal = booking.services.reduce(
      (sum, service) => sum + service.price * service.quantity,
      0
    )

    // Add travel fee
    const travelFee = calculateTravelFee()
    const subtotalWithTravel = servicesSubtotal + travelFee

    // Apply admin discount
    const subtotalAfterDiscount = subtotalWithTravel - invoiceSettings.discountAmount

    // Calculate tax on the subtotal (8% tax rate)
    const taxAmount = Math.max(subtotalAfterDiscount, 0) * 0.08

    // Final total including tax
    const totalWithTax = Math.max(subtotalAfterDiscount, 0) + taxAmount

    return totalWithTax
  }

  const calculateBalanceDue = () => {
    const adjustedTotal = calculateTotalWithAdjustments()
    const balanceDue =
      adjustedTotal - (invoiceSettings.depositPaid ? invoiceSettings.depositAmount : 0)
    return Math.max(balanceDue, 0)
  }

  const handleGenerateInvoice = async (format: 'html' | 'pdf') => {
    if (!booking) return

    setGenerating(true)
    try {
      const queryParams = new URLSearchParams({
        format: format === 'pdf' ? 'pdf' : 'html',
        depositAmount: invoiceSettings.depositAmount.toString(),
        depositPaid: invoiceSettings.depositPaid.toString(),
        additionalNotes: invoiceSettings.additionalNotes,
        paymentTerms: invoiceSettings.paymentTerms,
        travelMiles: invoiceSettings.travelMiles.toString(),
        discountAmount: invoiceSettings.discountAmount.toString(),
        discountDescription: invoiceSettings.discountDescription
      })

      const url = `/api/v1/bookings/${bookingId}/invoice?${queryParams.toString()}`

      if (format === 'pdf') {
        // Download PDF
        const response = await fetch(url)
        const blob = await response.blob()
        const downloadUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = `MyHibachi-Invoice-${booking.confirmationNumber}.pdf`
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(downloadUrl)
      } else {
        // Open in new tab
        window.open(url, '_blank')
      }
    } catch (error) {
      console.error('Error generating invoice:', error)
      alert('Error generating invoice. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading booking details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!booking) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Booking Not Found</h2>
          <p className="text-gray-600">Could not find booking with ID: {bookingId}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Generate Invoice</h1>
        <p className="text-gray-600">
          Create and customize invoice for booking #{booking.confirmationNumber}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Booking Details */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Booking Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-gray-500">Customer</Label>
                  <p className="font-semibold">{booking.customerName}</p>
                  <p className="text-sm text-gray-600">{booking.customerEmail}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Event Date</Label>
                  <p className="font-semibold">
                    {new Date(booking.eventDate).toLocaleDateString()} at {booking.eventTime}
                  </p>
                  <p className="text-sm text-gray-600">{booking.guestCount} guests</p>
                </div>
              </div>

              <div>
                <Label className="text-sm font-medium text-gray-500">Venue Address</Label>
                <p className="text-sm">
                  {booking.venueAddress.street}
                  <br />
                  {booking.venueAddress.city}, {booking.venueAddress.state}{' '}
                  {booking.venueAddress.zipcode}
                </p>
              </div>

              <div>
                <Label className="text-sm font-medium text-gray-500">Payment Status</Label>
                <div className="mt-1">
                  <Badge variant={booking.paymentStatus === 'paid' ? 'default' : 'secondary'}>
                    {booking.paymentStatus.toUpperCase()}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Services Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Services & Pricing
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {booking.services.map((service, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0"
                  >
                    <div className="flex-1">
                      <p className="font-medium">{service.name}</p>
                      <p className="text-sm text-gray-600">{service.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">
                        {service.quantity} × ${service.price.toFixed(2)}
                      </p>
                      <p className="text-sm text-gray-600">
                        ${(service.price * service.quantity).toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}

                <div className="pt-4 space-y-2">
                  <div className="flex justify-between font-medium">
                    <span>Services Subtotal:</span>
                    <span>
                      $
                      {booking.services
                        .reduce((sum, service) => sum + service.price * service.quantity, 0)
                        .toFixed(2)}
                    </span>
                  </div>

                  <p className="text-sm text-gray-500 italic">
                    * Final totals with travel fees, discounts, and tax are calculated in the
                    Payment Summary below
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Invoice Settings */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Deposit & Payment Settings
              </CardTitle>
              <CardDescription>
                Configure deposit information and payment terms for this invoice
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Deposit Amount */}
              <div className="space-y-2">
                <Label htmlFor="depositAmount">Deposit Amount ($)</Label>
                <Input
                  id="depositAmount"
                  type="number"
                  min="0"
                  max={booking.totalAmount}
                  step="0.01"
                  value={invoiceSettings.depositAmount || ''}
                  onChange={e => {
                    const value = e.target.value
                    // Prevent leading zeros and ensure valid number
                    const numValue = value === '' ? 0 : parseFloat(value.replace(/^0+/, '') || '0')
                    setInvoiceSettings(prev => ({
                      ...prev,
                      depositAmount: isNaN(numValue) ? 0 : Math.max(0, numValue)
                    }))
                  }}
                  placeholder="0.00"
                />
                <p className="text-sm text-gray-500">
                  Enter the deposit amount required (max: ${booking.totalAmount.toFixed(2)})
                </p>
              </div>

              {/* Deposit Status */}
              <div className="space-y-3">
                <Label>Deposit Status</Label>
                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="depositStatus"
                      checked={!invoiceSettings.depositPaid}
                      onChange={() => setInvoiceSettings(prev => ({ ...prev, depositPaid: false }))}
                      className="w-4 h-4 text-red-600 border-gray-300 focus:ring-red-500"
                    />
                    <span className="flex items-center gap-1 text-sm font-medium">
                      <AlertCircle className="h-4 w-4 text-red-500" />
                      Not Paid
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="depositStatus"
                      checked={invoiceSettings.depositPaid}
                      onChange={() => setInvoiceSettings(prev => ({ ...prev, depositPaid: true }))}
                      className="w-4 h-4 text-green-600 border-gray-300 focus:ring-green-500"
                    />
                    <span className="flex items-center gap-1 text-sm font-medium">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Paid
                    </span>
                  </label>
                </div>
              </div>

              {/* Travel Fee */}
              <div className="space-y-2">
                <Label htmlFor="travelMiles">Travel Distance (Miles)</Label>
                <Input
                  id="travelMiles"
                  type="number"
                  min="0"
                  step="0.1"
                  value={invoiceSettings.travelMiles || ''}
                  onChange={e => {
                    const value = e.target.value
                    const numValue = value === '' ? 0 : parseFloat(value.replace(/^0+/, '') || '0')
                    setInvoiceSettings(prev => ({
                      ...prev,
                      travelMiles: isNaN(numValue) ? 0 : Math.max(0, numValue)
                    }))
                  }}
                  placeholder="0.0"
                />
                <p className="text-sm text-gray-500">
                  Travel fee: ${calculateTravelFee().toFixed(2)} ($2 per mile)
                </p>
              </div>

              {/* Discount */}
              <div className="space-y-2">
                <Label htmlFor="discountAmount">Discount Amount ($)</Label>
                <div className="space-y-2">
                  <Input
                    id="discountAmount"
                    type="number"
                    min="0"
                    step="0.01"
                    value={invoiceSettings.discountAmount || ''}
                    onChange={e => {
                      const value = e.target.value
                      const numValue =
                        value === '' ? 0 : parseFloat(value.replace(/^0+/, '') || '0')
                      setInvoiceSettings(prev => ({
                        ...prev,
                        discountAmount: isNaN(numValue) ? 0 : Math.max(0, numValue)
                      }))
                    }}
                    placeholder="0.00"
                  />
                  <Input
                    id="discountDescription"
                    value={invoiceSettings.discountDescription}
                    onChange={e =>
                      setInvoiceSettings(prev => ({
                        ...prev,
                        discountDescription: e.target.value
                      }))
                    }
                    placeholder="Discount description (e.g., First time customer, Bulk order)"
                  />
                </div>
                <p className="text-sm text-gray-500">Enter discount amount and description</p>
              </div>

              {/* Payment Terms */}
              <div className="space-y-2">
                <Label htmlFor="paymentTerms">Payment Terms</Label>
                <Input
                  id="paymentTerms"
                  value={invoiceSettings.paymentTerms}
                  onChange={e =>
                    setInvoiceSettings(prev => ({
                      ...prev,
                      paymentTerms: e.target.value
                    }))
                  }
                  placeholder="Due upon service completion"
                />
              </div>

              {/* Additional Notes */}
              <div className="space-y-2">
                <Label htmlFor="additionalNotes">Additional Notes</Label>
                <Textarea
                  id="additionalNotes"
                  value={invoiceSettings.additionalNotes}
                  onChange={e =>
                    setInvoiceSettings(prev => ({
                      ...prev,
                      additionalNotes: e.target.value
                    }))
                  }
                  placeholder="Any special instructions or notes for this invoice..."
                  rows={3}
                />
              </div>

              {/* Balance Calculation */}
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <h4 className="font-semibold text-gray-900">Payment Summary</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Services Subtotal:</span>
                    <span>
                      $
                      {booking.services
                        .reduce((sum, service) => sum + service.price * service.quantity, 0)
                        .toFixed(2)}
                    </span>
                  </div>

                  {invoiceSettings.travelMiles > 0 && (
                    <div className="flex justify-between text-blue-600">
                      <span>Travel Fee ({invoiceSettings.travelMiles} mi × $2):</span>
                      <span>+${calculateTravelFee().toFixed(2)}</span>
                    </div>
                  )}

                  {invoiceSettings.discountAmount > 0 && (
                    <div className="flex justify-between text-green-600">
                      <span>Discount ({invoiceSettings.discountDescription || 'Applied'}):</span>
                      <span>-${invoiceSettings.discountAmount.toFixed(2)}</span>
                    </div>
                  )}

                  <div className="flex justify-between text-orange-600">
                    <span>Tax (8%):</span>
                    <span>+${calculateTax().toFixed(2)}</span>
                  </div>

                  <div className="flex justify-between font-medium border-t pt-1">
                    <span>Total Amount:</span>
                    <span>${calculateTotalWithAdjustments().toFixed(2)}</span>
                  </div>

                  {invoiceSettings.depositAmount > 0 && (
                    <div className="flex justify-between">
                      <span>Deposit {invoiceSettings.depositPaid ? '(Paid)' : '(Required)'}:</span>
                      <span>${invoiceSettings.depositAmount.toFixed(2)}</span>
                    </div>
                  )}

                  <div className="flex justify-between font-semibold border-t pt-1">
                    <span>Balance Due:</span>
                    <span
                      className={calculateBalanceDue() === 0 ? 'text-green-600' : 'text-orange-600'}
                    >
                      ${calculateBalanceDue().toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Generate Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Generate Invoice
              </CardTitle>
              <CardDescription>Create the invoice with your specified settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Button
                  onClick={() => handleGenerateInvoice('html')}
                  disabled={generating}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Eye className="h-4 w-4" />
                  Preview HTML
                </Button>

                <Button
                  onClick={() => handleGenerateInvoice('pdf')}
                  disabled={generating}
                  className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600"
                >
                  <Download className="h-4 w-4" />
                  Download PDF
                </Button>
              </div>

              {generating && (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-orange-500 mx-auto mb-2"></div>
                  <p className="text-sm text-gray-600">Generating invoice...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
