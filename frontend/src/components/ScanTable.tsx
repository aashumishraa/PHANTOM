import { Box, Badge, Heading, Table, Tbody, Td, Th, Thead, Tr, useColorModeValue } from '@chakra-ui/react'

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
}

export default function ScanTable({ data }: ScanTableProps) {
  const rowHover = useColorModeValue('whiteAlpha.100', 'whiteAlpha.100')
  const cardBg = useColorModeValue('whiteAlpha.100', 'whiteAlpha.100')

  return (
    <Box bg={cardBg} borderRadius="3xl" p={5} boxShadow="xl" border="1px solid" borderColor="whiteAlpha.100" overflowX="auto">
      <Heading size="sm" mb={4} color="gray.100">
        Recent Scans
      </Heading>
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
            <Tr key={scan.id} _hover={{ bg: rowHover }} transition="background 0.2s">
              <Td>{scan.id}</Td>
              <Td>{scan.url}</Td>
              <Td>{scan.timestamp}</Td>
              <Td>
                <Badge colorScheme={statusMap[scan.status] ?? 'gray'}>{scan.status}</Badge>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  )
}
