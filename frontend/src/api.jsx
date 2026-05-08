import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const API = import.meta.env.VITE_API_URL || '/api'

async function apiFetch(url, options) {
  const res = await fetch(API + url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new Error(data?.error || data?.message || `HTTP ${res.status}`)
  return data
}

function post(url, body) {
  return apiFetch(url, { method: 'POST', body: JSON.stringify(body) })
}

// Queries
export function useServices() {
  return useQuery({
    queryKey: ['services'],
    queryFn: () => apiFetch('/services'),
    refetchInterval: 60000, // Poll every 60s instead of 10s
  })
}

export function useCryptoParams() {
  return useQuery({
    queryKey: ['cryptoParams'],
    queryFn: () => apiFetch('/crypto_params'),
  })
}

export function useCommissionerState() {
  return useQuery({
    queryKey: ['commissionerState'],
    queryFn: () => apiFetch('/commissioner/state'),
    refetchInterval: 30000, // Poll every 30s instead of 5s
  })
}

export function useAdminState() {
  return useQuery({
    queryKey: ['adminState'],
    queryFn: () => apiFetch('/administrator/state'),
  })
}

export function useCounterState() {
  return useQuery({
    queryKey: ['counterState'],
    queryFn: () => apiFetch('/counter/state'),
    refetchInterval: 30000, 
  })
}

// Mutations
export function useInitKeys() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const [admin, counter] = await Promise.all([
        post('/administrator/generate_keys', { bits: 2048 }),
        post('/counter/generate_keys', { bits: 2048 }),
      ])
      return { admin, counter }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cryptoParams'] }),
  })
}

export function useResetAll() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => post('/reset_all', {}),
    onSuccess: () => qc.invalidateQueries(),
  })
}

export function useSetupCommissioner() {
  return useMutation({
    mutationFn: ({ title, candidates }) => post('/commissioner/setup', { title, candidates }),
  })
}

export function useRegisterVoter() {
  return useMutation({
    mutationFn: ({ name, email }) => post('/commissioner/register_voter', { name, email }),
  })
}

export function useBulkRegisterVoters() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file) => {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(API + '/commissioner/bulk_register_voters', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json().catch(() => null)
      if (!res.ok) throw new Error(data?.error || data?.message || `HTTP ${res.status}`)
      return data
    },
  })
}

export function useOpenVoting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => post('/commissioner/open_voting', {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['commissionerState'] }),
  })
}

export function useCloseVoting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const closeRes = await post('/commissioner/close_voting', {})
      const countRes = await post('/counter/count_votes', {})
      return { closeRes, countRes }
    },
    onSuccess: () => qc.invalidateQueries(),
  })
}

export function useValidateN1() {
  return useMutation({
    mutationFn: ({ N1 }) => post('/commissioner/validate_N1_check', { N1 }),
  })
}

export function useSignBlind() {
  return useMutation({
    mutationFn: ({ N1, m_masked }) => post('/administrator/sign_blind', { N1, m_masked }),
  })
}

export function useSubmitVote() {
  return useMutation({
    mutationFn: (ballot) => post('/vote/submit', ballot),
  })
}

export function useForwardBallots() {
  return useMutation({
    mutationFn: () => post('/forward_all_ballots', {}),
  })
}
