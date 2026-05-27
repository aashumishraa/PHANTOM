import { Box, SimpleGrid, Stat, StatLabel, StatNumber, StatHelpText, Badge, useColorModeValue } from '@chakra-ui/react'

export type StatsOverviewProps = {
  totalScans: number
  activeThreats: number
  uptime: string
  avgRisk: number
  isLoading: boolean
}

export default function StatsOverview({ totalScans, activeThreats, uptime, avgRisk, isLoading }: StatsOverviewProps) {
  const cardBg = useColorModeValue('whiteAlpha.100', 'whiteAlpha.100')
  const accent = 'brand.400'

  const items = [
    { label: 'Total Scans', value: totalScans.toString(), help: 'Last 30 days' },
    { label: 'Active Threats', value: activeThreats.toString(), help: 'Realtime alerts' },
    { label: 'System Uptime', value: uptime, help: 'Since last restart' },
    { label: 'Avg. Risk Score', value: `${avgRisk}%`, help: 'Lower is better' },
  ]

  return (
    <SimpleGrid columns={{ base: 1, md: 4 }} minChildWidth="220px" spacing={4}>
      {items.map((item) => (
        <Box key={item.label} bg={cardBg} borderRadius="3xl" p={5} boxShadow="xl" border="1px solid" borderColor="whiteAlpha.100">
          <Stat>
            <StatLabel color="gray.400">{item.label}</StatLabel>
            <StatNumber color={accent} fontSize="3xl">
              {isLoading ? '…' : item.value}
            </StatNumber>
            <StatHelpText color="gray.500">{item.help}</StatHelpText>
          </Stat>
          {item.label === 'Active Threats' && !isLoading && (
            <Badge mt={3} colorScheme={activeThreats > 5 ? 'red' : 'green'}>
              {activeThreats > 5 ? 'High' : 'Normal'}
            </Badge>
          )}
        </Box>
      ))}
    </SimpleGrid>
  )
}
