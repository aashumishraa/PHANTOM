import { Box, Badge, Heading, Table, Tbody, Td, Th, Thead, Tr, useColorModeValue, Text, Tooltip } from '@chakra-ui/react'

export type ScanRecord = {
  id: string
  url: string
  timestamp: string
  status: 'Success' | 'Warning' | 'Danger' | string
}

const statusMap: Record<string, string> = {
  Success: 'green',
  Warning: 'yellow',
  Danger: 'red',
}

export type ScanTableProps = {
  data: ScanRecord[]
  onRowClick?: (scan: ScanRecord) => void
}

export default function ScanTable({ data, onRowClick }: ScanTableProps) {
  const rowHover = useColorModeValue('whiteAlpha.100', 'whiteAlpha.100')
  const cardBg = useColorModeValue('whiteAlpha.100', 'whiteAlpha.100')

  return (
    <Box bg={cardBg} borderRadius="3xl" p={5} boxShadow="xl" border="1px solid" borderColor="whiteAlpha.100" overflowX="auto">
      <Heading size="sm" mb={1} color="gray.100">
        Recent Scans
      </Heading>
      <Text color="gray.500" fontSize="xs" mb={4}>Click a row to view the full vulnerability report</Text>
      <Table variant="striped" colorScheme="cyan" size="sm">
        <Thead>
          <Tr>
            <Th color="gray.400">Scan ID</Th>
            <Th color="gray.400">Target URL</Th>
            <Th color="gray.400">Timestamp</Th>
            <Th color="gray.400">Status</Th>
          </Tr>
        </Thead>
        <Tbody>
          {data.map((scan) => (
            <Tooltip key={scan.id} label={scan.id.startsWith('F-') ? 'Placeholder record' : 'Click to view report'} placement="top">
              <Tr
                _hover={{ bg: rowHover, transform: 'scale(1.005)' }}
                transition="all 0.15s ease"
                cursor={onRowClick ? 'pointer' : 'default'}
                onClick={() => onRowClick?.(scan)}
              >
                <Td fontFamily="mono" fontSize="xs" color="cyan.300" maxW="180px" isTruncated>{scan.id}</Td>
                <Td>{scan.url}</Td>
                <Td>{scan.timestamp}</Td>
                <Td>
                  <Badge colorScheme={statusMap[scan.status] ?? 'gray'}>{scan.status}</Badge>
                </Td>
              </Tr>
            </Tooltip>
          ))}
        </Tbody>
      </Table>
    </Box>
  )
}
