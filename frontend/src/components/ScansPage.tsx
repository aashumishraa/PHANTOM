import {
  Box, Heading, Text, VStack, HStack, Badge, Flex, Divider,
  Table, Thead, Tbody, Tr, Th, Td, Tooltip, Input, InputGroup,
  InputLeftElement, Button
} from '@chakra-ui/react'
import { SearchIcon, AddIcon } from '@chakra-ui/icons'
import type { ScanRecord } from './ScanTable'

type ScansPageProps = {
  scans: ScanRecord[]
  query: string
  onQueryChange: (v: string) => void
  onSubmit: () => void
  isLoading: boolean
  onRowClick: (scan: ScanRecord) => void
}

const statusColor: Record<string, string> = {
  Success: 'green',
  Warning: 'yellow',
  Danger: 'red',
}

export default function ScansPage({ scans, query, onQueryChange, onSubmit, isLoading, onRowClick }: ScansPageProps) {
  return (
    <VStack align="stretch" spacing={6}>
      <Box bg="gray.800" borderRadius="3xl" p={6} boxShadow="2xl" border="1px solid" borderColor="whiteAlpha.100">
        <Flex justify="space-between" align="center" mb={2}>
          <Box>
            <Text color="cyan.400" fontWeight="bold" textTransform="uppercase" letterSpacing="widest" fontSize="xs">Security</Text>
            <Heading size="lg" color="white">Scan Management</Heading>
            <Text color="gray.400" mt={1} fontSize="sm">Launch new scans and browse all historical results.</Text>
          </Box>
          <Badge colorScheme="cyan" fontSize="sm" px={3} py={1} borderRadius="full">{scans.length} total</Badge>
        </Flex>

        <Divider my={5} borderColor="whiteAlpha.100" />

        {/* New Scan Input */}
        <HStack spacing={3}>
          <InputGroup flex={1}>
            <InputLeftElement pointerEvents="none" children={<SearchIcon color="gray.400" />} />
            <Input
              value={query}
              onChange={e => onQueryChange(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && onSubmit()}
              placeholder="https://target.example.com"
              bg="whiteAlpha.100"
              color="gray.100"
              border="1px solid"
              borderColor="whiteAlpha.200"
              _focus={{ borderColor: 'cyan.400', boxShadow: '0 0 0 1px #22d3ee' }}
            />
          </InputGroup>
          <Button
            colorScheme="cyan"
            leftIcon={<AddIcon />}
            onClick={onSubmit}
            isLoading={isLoading}
            loadingText="Scanning"
            minW="160px"
            _hover={{ transform: 'translateY(-1px)', boxShadow: '0 4px 20px rgba(34,211,238,0.3)' }}
            transition="all 0.2s ease"
          >
            Initiate Scan
          </Button>
        </HStack>
      </Box>

      {/* All scans table */}
      <Box bg="gray.800" borderRadius="3xl" p={6} boxShadow="xl" border="1px solid" borderColor="whiteAlpha.100" overflowX="auto">
        <Heading size="sm" mb={1} color="gray.100">All Scans</Heading>
        <Text color="gray.500" fontSize="xs" mb={4}>Click any row to view the full vulnerability report</Text>
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th color="gray.400" borderColor="whiteAlpha.100">#</Th>
              <Th color="gray.400" borderColor="whiteAlpha.100">Scan ID</Th>
              <Th color="gray.400" borderColor="whiteAlpha.100">Target URL</Th>
              <Th color="gray.400" borderColor="whiteAlpha.100">Timestamp</Th>
              <Th color="gray.400" borderColor="whiteAlpha.100">Status</Th>
            </Tr>
          </Thead>
          <Tbody>
            {scans.map((scan, i) => (
              <Tooltip key={scan.id} label={scan.id.startsWith('F-') ? 'Placeholder' : 'Click to view report'} placement="top">
                <Tr
                  _hover={{ bg: 'whiteAlpha.100', cursor: 'pointer' }}
                  transition="all 0.15s"
                  onClick={() => onRowClick(scan)}
                >
                  <Td color="gray.600" borderColor="whiteAlpha.50">{i + 1}</Td>
                  <Td fontFamily="mono" fontSize="xs" color="cyan.300" maxW="200px" isTruncated borderColor="whiteAlpha.50">{scan.id}</Td>
                  <Td color="gray.200" borderColor="whiteAlpha.50">{scan.url}</Td>
                  <Td color="gray.400" fontSize="xs" borderColor="whiteAlpha.50">{scan.timestamp}</Td>
                  <Td borderColor="whiteAlpha.50">
                    <Badge colorScheme={statusColor[scan.status] ?? 'gray'}>{scan.status}</Badge>
                  </Td>
                </Tr>
              </Tooltip>
            ))}
          </Tbody>
        </Table>
      </Box>
    </VStack>
  )
}
