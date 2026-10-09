import { create } from "zustand";

interface UiState {
  selectedTxId: string | null;
  isPinned: boolean;
  statusFilter: string | null;
  setSelectedTxId: (id: string | null) => void;
  setIsPinned: (pinned: boolean) => void;
  setStatusFilter: (filter: string | null) => void;
}

export const useUiStore = create<UiState>((set) => ({
  selectedTxId: null,
  isPinned: false,
  statusFilter: null,
  setSelectedTxId: (selectedTxId) => set({ selectedTxId }),
  setIsPinned: (isPinned) => set({ isPinned }),
  setStatusFilter: (statusFilter) => set({ statusFilter }),
}));
