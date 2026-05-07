import { create } from 'zustand'

export const useElectionStore = create((set) => ({
  cards: [],
  total: 0,
  title: '',
  setSession: (cards, total, title) => set({ cards, total, title }),
  clearSession: () => set({ cards: [], total: 0, title: '' }),
}))
