'use client';

import { Copy, Edit, Eye, MoreVertical, Send, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface Campaign {
  id: string;
  name: string;
  subject: string;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'failed';
  recipients: number;
  sentAt?: string;
  scheduledFor?: string;
  stats?: {
    sent: number;
    opened: number;
    clicked: number;
    bounced: number;
  };
}

export default function CampaignList({ onCreateNew }: { onCreateNew: () => void }) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const response = await fetch('/api/newsletter/campaigns');
      const data = await response.json();
      setCampaigns(data);
    } catch (error) {
      console.error('Failed to fetch campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: Campaign['status']) => {
    const variants: Record<
      Campaign['status'],
      { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }
    > = {
      draft: { variant: 'secondary', label: 'Draft' },
      scheduled: { variant: 'default', label: 'Scheduled' },
      sending: { variant: 'default', label: 'Sending...' },
      sent: { variant: 'outline', label: 'Sent' },
      failed: { variant: 'destructive', label: 'Failed' },
    };
    const config = variants[status];
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  if (loading) {
    return <Card><CardContent className="py-8 text-center">Loading campaigns...</CardContent></Card>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Campaigns</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Campaign Name</TableHead>
              <TableHead>Subject</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Recipients</TableHead>
              <TableHead>Open Rate</TableHead>
              <TableHead>Click Rate</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {campaigns.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                  No campaigns yet. <Button variant="link" onClick={onCreateNew}>Create your first campaign</Button>
                </TableCell>
              </TableRow>
            ) : (
              campaigns.map((campaign) => (
                <TableRow key={campaign.id}>
                  <TableCell className="font-medium">{campaign.name}</TableCell>
                  <TableCell>{campaign.subject}</TableCell>
                  <TableCell>{getStatusBadge(campaign.status)}</TableCell>
                  <TableCell>{campaign.recipients.toLocaleString()}</TableCell>
                  <TableCell>
                    {campaign.stats ? 
                      `${((campaign.stats.opened / campaign.stats.sent) * 100).toFixed(1)}%` : 
                      '-'
                    }
                  </TableCell>
                  <TableCell>
                    {campaign.stats ? 
                      `${((campaign.stats.clicked / campaign.stats.sent) * 100).toFixed(1)}%` : 
                      '-'
                    }
                  </TableCell>
                  <TableCell>
                    {campaign.sentAt 
                      ? formatDistanceToNow(new Date(campaign.sentAt), { addSuffix: true })
                      : campaign.scheduledFor
                      ? `Scheduled for ${formatDistanceToNow(new Date(campaign.scheduledFor), { addSuffix: true })}`
                      : 'Draft'
                    }
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        {campaign.status === 'draft' && (
                          <>
                            <DropdownMenuItem>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Send className="mr-2 h-4 w-4" />
                              Send Now
                            </DropdownMenuItem>
                          </>
                        )}
                        <DropdownMenuItem>
                          <Copy className="mr-2 h-4 w-4" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive">
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
