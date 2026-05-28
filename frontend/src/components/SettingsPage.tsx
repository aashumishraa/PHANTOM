import {
  Box, Heading, Text, VStack, HStack, Badge, Flex, Divider,
  Switch, FormControl, FormLabel, Select, Input, Button,
  SimpleGrid, Tag, useToast, Slider, SliderTrack, SliderFilledTrack,
  SliderThumb, Tooltip as ChakraTooltip
} from '@chakra-ui/react'
import { useState } from 'react'
import { FiSave, FiRefreshCw } from 'react-icons/fi'

export default function SettingsPage() {
  const toast = useToast()
  const [apiBase, setApiBase] = useState('http://127.0.0.1:8000')
  const [scanMode, setScanMode] = useState('quick')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [wsEnabled, setWsEnabled] = useState(true)
  const [notifications, setNotifications] = useState(true)
  const [timeout, setTimeout] = useState(30)
  const [showTooltip, setShowTooltip] = useState(false)

  const handleSave = () => {
    toast({
      title: '✅ Settings saved',
      description: 'Your configuration has been applied.',
      status: 'success',
      duration: 3000,
      isClosable: true,
    })
  }

  const handleReset = () => {
    setApiBase('http://127.0.0.1:8000')
    setScanMode('quick')
    setAutoRefresh(true)
    setWsEnabled(true)
    setNotifications(true)
    setTimeout(30)
    toast({
      title: 'Settings reset to defaults',
      status: 'info',
      duration: 2000,
      isClosable: true,
    })
  }

  return (
    <VStack align="stretch" spacing={6}>
      {/* Header */}
      <Box bg="gray.800" borderRadius="3xl" p={6} boxShadow="2xl" border="1px solid" borderColor="whiteAlpha.100">
        <Flex justify="space-between" align="center">
          <Box>
            <Text color="purple.400" fontWeight="bold" textTransform="uppercase" letterSpacing="widest" fontSize="xs">Configuration</Text>
            <Heading size="lg" color="white">Settings</Heading>
            <Text color="gray.400" mt={1} fontSize="sm">Configure PHANTOM's backend connection, scan behaviour, and notification preferences.</Text>
          </Box>
          <HStack spacing={3}>
            <Button leftIcon={<FiRefreshCw />} variant="ghost" colorScheme="gray" size="sm" onClick={handleReset}>
              Reset
            </Button>
            <Button leftIcon={<FiSave />} colorScheme="cyan" size="sm" onClick={handleSave}
              _hover={{ transform: 'translateY(-1px)', boxShadow: '0 4px 20px rgba(34,211,238,0.3)' }}
              transition="all 0.2s"
            >
              Save Changes
            </Button>
          </HStack>
        </Flex>
      </Box>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={5}>
        {/* Backend Connection */}
        <Box bg="gray.800" borderRadius="2xl" p={6} border="1px solid" borderColor="whiteAlpha.100">
          <HStack mb={4}>
            <Tag colorScheme="cyan" borderRadius="full" size="sm">Connection</Tag>
            <Heading size="sm" color="gray.100">Backend API</Heading>
          </HStack>
          <Divider borderColor="whiteAlpha.100" mb={4} />
          <VStack align="stretch" spacing={4}>
            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">API Base URL</FormLabel>
              <Input
                value={apiBase}
                onChange={e => setApiBase(e.target.value)}
                bg="whiteAlpha.50"
                border="1px solid"
                borderColor="whiteAlpha.200"
                color="gray.100"
                fontFamily="mono"
                fontSize="sm"
                _focus={{ borderColor: 'cyan.400' }}
              />
              <Text color="gray.600" fontSize="xs" mt={1}>FastAPI server endpoint (default: localhost:8000)</Text>
            </FormControl>

            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">Request Timeout (seconds)</FormLabel>
              <ChakraTooltip label={`${timeout}s`} isOpen={showTooltip} placement="top">
                <Slider
                  min={5} max={120} step={5}
                  value={timeout}
                  onChange={v => setTimeout(v)}
                  onMouseEnter={() => setShowTooltip(true)}
                  onMouseLeave={() => setShowTooltip(false)}
                >
                  <SliderTrack bg="whiteAlpha.200">
                    <SliderFilledTrack bg="cyan.400" />
                  </SliderTrack>
                  <SliderThumb boxSize={4} bg="cyan.300" />
                </Slider>
              </ChakraTooltip>
              <Text color="gray.600" fontSize="xs" mt={1}>Current: {timeout} seconds</Text>
            </FormControl>
          </VStack>
        </Box>

        {/* Scan Defaults */}
        <Box bg="gray.800" borderRadius="2xl" p={6} border="1px solid" borderColor="whiteAlpha.100">
          <HStack mb={4}>
            <Tag colorScheme="orange" borderRadius="full" size="sm">Scanning</Tag>
            <Heading size="sm" color="gray.100">Scan Defaults</Heading>
          </HStack>
          <Divider borderColor="whiteAlpha.100" mb={4} />
          <VStack align="stretch" spacing={4}>
            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">Default Scan Mode</FormLabel>
              <Select
                value={scanMode}
                onChange={e => setScanMode(e.target.value)}
                bg="whiteAlpha.50"
                border="1px solid"
                borderColor="whiteAlpha.200"
                color="gray.100"
                _focus={{ borderColor: 'cyan.400' }}
              >
                <option value="quick" style={{ background: '#1a202c' }}>Quick — Fast passive scan</option>
                <option value="deep" style={{ background: '#1a202c' }}>Deep — Full active scan suite</option>
              </Select>
            </FormControl>

            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel color="gray.300" fontSize="sm" mb={0}>WebSocket Live Stream</FormLabel>
                <Text color="gray.600" fontSize="xs">Show real-time terminal output during scans</Text>
              </Box>
              <Switch colorScheme="cyan" isChecked={wsEnabled} onChange={e => setWsEnabled(e.target.checked)} />
            </FormControl>
          </VStack>
        </Box>

        {/* Notifications */}
        <Box bg="gray.800" borderRadius="2xl" p={6} border="1px solid" borderColor="whiteAlpha.100">
          <HStack mb={4}>
            <Tag colorScheme="green" borderRadius="full" size="sm">Alerts</Tag>
            <Heading size="sm" color="gray.100">Notifications</Heading>
          </HStack>
          <Divider borderColor="whiteAlpha.100" mb={4} />
          <VStack align="stretch" spacing={4}>
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel color="gray.300" fontSize="sm" mb={0}>Scan Completion Alerts</FormLabel>
                <Text color="gray.600" fontSize="xs">Toast notification when a scan finishes</Text>
              </Box>
              <Switch colorScheme="cyan" isChecked={notifications} onChange={e => setNotifications(e.target.checked)} />
            </FormControl>
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel color="gray.300" fontSize="sm" mb={0}>Auto-refresh Dashboard</FormLabel>
                <Text color="gray.600" fontSize="xs">Periodically re-check backend health</Text>
              </Box>
              <Switch colorScheme="cyan" isChecked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
            </FormControl>
          </VStack>
        </Box>

        {/* System Info */}
        <Box bg="gray.800" borderRadius="2xl" p={6} border="1px solid" borderColor="whiteAlpha.100">
          <HStack mb={4}>
            <Tag colorScheme="purple" borderRadius="full" size="sm">System</Tag>
            <Heading size="sm" color="gray.100">About PHANTOM</Heading>
          </HStack>
          <Divider borderColor="whiteAlpha.100" mb={4} />
          <VStack align="stretch" spacing={3}>
            {[
              ['Version', 'v1.0.0'],
              ['Backend', 'FastAPI + Uvicorn'],
              ['Scanner Engines', 'Nuclei + OWASP ZAP'],
              ['AI Model', 'Gemini 2.5 Flash'],
              ['Frontend', 'React 18 + Vite + ChakraUI'],
              ['WebSocket', 'ws://localhost:8000/ws/stream/{id}'],
            ].map(([label, value]) => (
              <Flex key={label} justify="space-between" align="center">
                <Text color="gray.500" fontSize="sm">{label}</Text>
                <Badge colorScheme="gray" fontFamily="mono" fontSize="xs">{value}</Badge>
              </Flex>
            ))}
          </VStack>
        </Box>
      </SimpleGrid>
    </VStack>
  )
}
