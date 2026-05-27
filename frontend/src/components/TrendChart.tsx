import { Box, Heading, useColorModeValue } from '@chakra-ui/react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export type TrendDataPoint = {
  date: string
  scans: number
}

export type TrendChartProps = {
  data: TrendDataPoint[]
}

export default function TrendChart({ data }: TrendChartProps) {
  const cardBg = useColorModeValue('whiteAlpha.100', 'whiteAlpha.100')

  return (
    <Box bg={cardBg} borderRadius="3xl" p={5} boxShadow="xl" border="1px solid" borderColor="whiteAlpha.100" minH="320px">
      <Heading size="sm" mb={4} color="gray.100">
        Scan Trends
      </Heading>
      <Box h="260px">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 0, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis dataKey="date" tick={{ fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <Tooltip wrapperStyle={{ background: '#0f172a', borderRadius: 12, border: '1px solid rgba(148, 163, 184, 0.12)' }} />
            <Area type="monotone" dataKey="scans" stroke="#22d3ee" fill="url(#trendFill)" strokeWidth={3} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  )
}
