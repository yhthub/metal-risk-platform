export const planStepKey = (step: { title: string }, index: number) => `${index}:${step.title}`

export function usePlanChecks() {
  const checked = useState<Record<string, string[]>>('intervention-work-checks', () => ({}))
  const isReviewed = (id: string, key: string) => checked.value[id]?.includes(key) ?? false
  function toggleReviewed(id: string, key: string) {
    const previous = checked.value[id] ?? []
    checked.value[id] = isReviewed(id, key) ? previous.filter(item => item !== key) : [...previous, key]
  }
  return { isReviewed, toggleReviewed }
}
