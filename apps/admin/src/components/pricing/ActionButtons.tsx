import { Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ActionButtonsProps {
  onEdit: () => void;
  onDelete: () => void;
  editLabel?: string;
  deleteLabel?: string;
}

export function ActionButtons({
  onEdit,
  onDelete,
  editLabel = 'Edit',
  deleteLabel = 'Delete',
}: ActionButtonsProps) {
  return (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="sm" onClick={onEdit}>
        <Edit className="w-4 h-4 mr-1" />
        {editLabel}
      </Button>
      <Button variant="destructive" size="sm" onClick={onDelete} className="bg-red-600 hover:bg-red-700 text-white">
        <Trash2 className="w-4 h-4 mr-1" />
        {deleteLabel}
      </Button>
    </div>
  );
}
