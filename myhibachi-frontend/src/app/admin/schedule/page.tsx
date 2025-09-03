import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/components/ui/button'

export default function SchedulePage() {
  const currentDate = new Date()
  const currentMonth = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  const scheduledEvents = [
    {
      id: 1,
      title: 'Johnson Anniversary Party',
      date: '2025-02-15',
      time: '6:00 PM - 9:00 PM',
      guests: 25,
      chef: 'Chef Takeshi',
      location: '123 Oak Street, City'
    },
    {
      id: 2,
      title: 'Corporate Team Building',
      date: '2025-02-18',
      time: '5:30 PM - 8:30 PM',
      guests: 40,
      chef: 'Chef Maria',
      location: '456 Business Plaza, City'
    },
    {
      id: 3,
      title: 'Birthday Celebration',
      date: '2025-02-20',
      time: '7:00 PM - 10:00 PM',
      guests: 15,
      chef: 'Chef David',
      location: '789 Residential Lane, City'
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Schedule</h1>
          <p className="text-gray-600">Manage chef schedules and event calendar</p>
        </div>
        <Button>
          <Calendar className="w-4 h-4 mr-2" />
          Add Event
        </Button>
      </div>

      {/* Calendar Header */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">{currentMonth}</h2>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm">
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm">
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Calendar Grid Placeholder */}
        <div className="grid grid-cols-7 gap-1 mb-4">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className="p-2 text-center text-sm font-medium text-gray-500">
              {day}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1">
          {Array.from({ length: 35 }, (_, i) => (
            <div key={i} className="aspect-square p-2 border border-gray-100 text-center text-sm">
              {i < 28 ? i + 1 : ''}
            </div>
          ))}
        </div>
      </div>

      {/* Upcoming Events */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Upcoming Events</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {scheduledEvents.map(event => (
            <div key={event.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900">{event.title}</h3>
                  <div className="mt-1 text-sm text-gray-500">
                    <p>
                      {event.date} • {event.time}
                    </p>
                    <p>
                      {event.guests} guests • {event.chef}
                    </p>
                    <p>{event.location}</p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button variant="outline" size="sm">
                    Edit
                  </Button>
                  <Button variant="outline" size="sm">
                    Details
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
