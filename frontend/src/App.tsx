import { useEffect, useState } from 'react'
import { useToast, Box, Flex, Heading, Text, VStack, Badge, useColorModeValue, SimpleGrid, Divider } from '@chakra-ui/react'
import axios from 'axios'
import Sidebar from './components/Sidebar'
import StatsOverview from './components/StatsOverview'
import TrendChart from './components/TrendChart'
import ScanTable from './components/ScanTable'
import type { ScanRecord } from './components/ScanTable'
import ActionCenter from './components/ActionCenter'
import './App.css'

const placeholderStats = {
  totalScans: 1280,
  activeThreats: 7,
  uptime: '99.98%',
  avgRisk: 61,
  trend: [420, 470, 520, 580, 620, 690, 705, 720, 710, 740, 760, 780, 790, 805, 820, 840, 860, 880, 900, 920, 930, 940, 950, 960, 970, 980, 990, 1005, 1020, 1035],
}

const placeholderScans: ScanRecord[] = [
  { id: 'F-893', url: 'https://example.com', timestamp: '2026-05-27 18:23', status: 'Success' },
  { id: 'F-901', url: 'https://demo.site', timestamp: '2026-05-27 17:11', status: 'Warning' },
  { id: 'F-772', url: 'https://app.site', timestamp: '2026-05-27 15:47', status: 'Danger' },
]

export default function App() {
  const [query, setQuery] = useState('')
  const [stats, setStats] = useState(placeholderStats)
  const [scans, setScans] = useState<ScanRecord[]>(placeholderScans)
  const [loading, setLoading] = useState(false)
  const [isInitiating, setIsInitiating] = useState(false)
  const [backendHealthy, setBackendHealthy] = useState(true)
  const toast = useToast()
  const pageBg = useColorModeValue('gray.950', 'gray.950')

  const apiBase = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

  const refreshDashboard = async () => {
    setLoading(true)
    try {
      const [statsRes, scansRes] = await Promise.all([
        axios.get(`${apiBase}/dashboard`),
        axios.get(`${apiBase}/recent`),
      ])

      setStats({
        totalScans: statsRes.data.totalScans ?? placeholderStats.totalScans,
        activeThreats: statsRes.data.activeThreats ?? placeholderStats.activeThreats,
        uptime: statsRes.data.uptime ?? placeholderStats.uptime,
        avgRisk: statsRes.data.avgRisk ?? placeholderStats.avgRisk,
        trend: statsRes.data.trend ?? placeholderStats.trend,
      })
      setScans(scansRes.data ?? placeholderScans)
      setBackendHealthy(true)
    } catch (error) {
      setBackendHealthy(false)
      toast({
        title: 'Unable to refresh dashboard',
        description: 'Using cached data while backend connectivity is restored.',
        status: 'warning',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refreshDashboard()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleInitiateScan = async () => {
    if (!query.trim()) {
      toast({
        title: 'Enter a target URL',
        status: 'info',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    setIsInitiating(true)
    try {
      const response = await axios.post(`${apiBase}/scan`, { url: query.trim() })
      setScans((current) => [
        {
          id: response.data.id ?? `Q-${Date.now()}`,
          url: query.trim(),
          timestamp: new Date().toLocaleString(),
          status: 'Warning',
        },
        ...current,
      ])
      toast({
        title: 'Scan initiated',
        description: 'The target scan has been submitted successfully.',
        status: 'success',
        duration: 4000,
        isClosable: true,
      })
      setQuery('')
    } catch (error) {
      toast({
        title: 'Scan failed',
        description: 'Unable to initiate scan. Check server connectivity.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsInitiating(false)
    }
  }

  return (
    <Box
      minH="100vh"
      bg={pageBg}
      bgGradient="radial(circle at top left, rgba(14, 165, 233, 0.14), transparent 26%), radial(circle at bottom right, rgba(59, 130, 246, 0.10), transparent 32%)"
      px={{ base: 4, md: 6 }}
      py={{ base: 4, md: 6 }}
    >
      <Flex direction={{ base: 'column', lg: 'row' }} gap={6} align="stretch">
        <Sidebar />

        <Box flex={1}>
          <VStack align="stretch" spacing={6}>
            <Box bg="gray.800" borderRadius="3xl" p={6} boxShadow="2xl" border="1px solid" borderColor="whiteAlpha.100">
              <Flex direction={{ base: 'column', md: 'row' }} align="center" justify="space-between" gap={4}>
                <Box>
                  <Text color="brand.400" fontWeight="bold" textTransform="uppercase" letterSpacing="widest" fontSize="sm">
                    PHANTOM Cyber Intelligence
                  </Text>
                  <Heading size="xl" letterSpacing="tight" color="whiteAlpha.900">
                    Live Threat Operations
                  </Heading>
                  <Text color="gray.300" mt={3} maxW="2xl" lineHeight="tall">
                    A unified security command center for scan orchestration, threat tracking, and operational alerting across your critical infrastructure.
                  </Text>
                </Box>

                <Box textAlign={{ base: 'left', md: 'right' }}>
                  <Badge colorScheme={backendHealthy ? 'green' : 'red'} variant="subtle" px={4} py={2} borderRadius="full" fontSize="sm">
                    {backendHealthy ? 'Backend Online' : 'Offline Mode'}
                  </Badge>
                  <Text color="gray.500" fontSize="sm" mt={2}>
                    Updated every time the dashboard refreshes.
                  </Text>
                </Box>
              </Flex>
            </Box>

            <SimpleGrid columns={{ base: 1, xl: 2 }} spacing={6}>
              <Box bg="gray.800" borderRadius="3xl" p={6} boxShadow="xl" border="1px solid" borderColor="whiteAlpha.100">
                <Heading size="md" mb={4} color="gray.100">
                  Operational Metrics
                </Heading>
                <StatsOverview
                  totalScans={stats.totalScans}
                  activeThreats={stats.activeThreats}
                  uptime={stats.uptime}
                  avgRisk={stats.avgRisk}
                  isLoading={loading}
                />
              </Box>

              <Box bg="gray.800" borderRadius="3xl" p={6} boxShadow="xl" border="1px solid" borderColor="whiteAlpha.100">
                <Heading size="md" mb={4} color="gray.100">
                  Network Scan Velocity
                </Heading>
                <TrendChart data={stats.trend.map((scansValue, index) => ({ date: `Day ${index + 1}`, scans: scansValue }))} />
              </Box>
            </SimpleGrid>

            <Box bg="gray.800" borderRadius="3xl" p={6} boxShadow="xl" border="1px solid" borderColor="whiteAlpha.100">
              <Flex direction={{ base: 'column', md: 'row' }} align="center" justify="space-between" gap={4}>
                <Box>
                  <Heading size="md" color="gray.100">
                    Action Center
                  </Heading>
                  <Text color="gray.400" mt={2}>
                    Initiate a targeted audit or expand coverage with a single command.
                  </Text>
                </Box>
                <Badge colorScheme="cyan" variant="subtle" px={4} py={2} borderRadius="full" fontSize="sm">
                  Ready for new scans
                </Badge>
              </Flex>
              <Divider my={6} borderColor="whiteAlpha.100" />
              <ActionCenter
                query={query}
                onQueryChange={setQuery}
                onSubmit={handleInitiateScan}
                isLoading={isInitiating}
              />
            </Box>

            <ScanTable data={scans} />
          </VStack>
        </Box>
      </Flex>
    </Box>
  )
}
