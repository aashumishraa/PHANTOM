import { Box, VStack, HStack, Avatar, Heading, Text, Badge, Button, Divider } from '@chakra-ui/react'
import { FiShield, FiActivity, FiBarChart2, FiSettings } from 'react-icons/fi'

export type PageName = 'Dashboard' | 'Scans' | 'Threats' | 'Settings'

const navItems: { label: PageName; icon: React.ElementType }[] = [
  { label: 'Dashboard', icon: FiBarChart2 },
  { label: 'Scans', icon: FiActivity },
  { label: 'Threats', icon: FiShield },
  { label: 'Settings', icon: FiSettings },
]

type SidebarProps = {
  activePage: PageName
  onNavigate: (page: PageName) => void
}

export default function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <Box
      minW={{ base: '100%', lg: '260px' }}
      bg="gray.900"
      boxShadow="2xl"
      borderRight="1px solid"
      borderColor="whiteAlpha.100"
      borderRadius={{ base: '2xl', lg: '3xl' }}
      p={6}
      h={{ base: 'auto', lg: 'calc(100vh - 32px)' }}
      position={{ lg: 'sticky' }}
      top={{ lg: '16px' }}
    >
      <VStack align="start" spacing={6} h="full">
        <VStack align="start" spacing={3}>
          <Avatar name="PHANTOM" bg="brand.400" color="gray.900" />
          <Box>
            <Text fontSize="sm" letterSpacing="widest" color="brand.400" textTransform="uppercase">
              PHANTOM
            </Text>
            <Heading size="md">Cyber Ops</Heading>
          </Box>
        </VStack>

        <Box bg="whiteAlpha.50" p={4} borderRadius="2xl" w="full">
          <HStack justify="space-between" spacing={3}>
            <Box>
              <Text fontSize="sm" color="gray.400">System Health</Text>
              <Heading size="sm">Operational</Heading>
            </Box>
            <Badge colorScheme="green" variant="subtle" px={3} py={1} borderRadius="full">
              Stable
            </Badge>
          </HStack>
        </Box>

        <Divider borderColor="whiteAlpha.100" />

        <VStack align="stretch" spacing={2} w="full">
          {navItems.map((item) => {
            const isActive = activePage === item.label
            return (
              <Button
                key={item.label}
                variant={isActive ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                w="full"
                gap={3}
                leftIcon={<item.icon />}
                colorScheme={isActive ? 'cyan' : 'gray'}
                bg={isActive ? 'rgba(34,211,238,0.12)' : undefined}
                color={isActive ? 'cyan.300' : 'gray.400'}
                borderRadius="2xl"
                borderLeft={isActive ? '3px solid' : '3px solid transparent'}
                borderLeftColor={isActive ? 'cyan.400' : 'transparent'}
                transition="all 0.2s ease"
                _hover={{
                  bg: isActive ? 'rgba(34,211,238,0.18)' : 'whiteAlpha.100',
                  color: 'white',
                  transform: 'translateX(3px)',
                }}
                onClick={() => onNavigate(item.label)}
              >
                {item.label}
              </Button>
            )
          })}
        </VStack>

        <Box mt="auto" bg="whiteAlpha.50" borderRadius="2xl" p={4} w="full">
          <Text fontSize="xs" color="gray.500" mb={1}>Active Page</Text>
          <Text fontSize="sm" color="cyan.300" fontWeight="bold">{activePage}</Text>
          <Text fontSize="xs" color="gray.600" mt={2}>Workload</Text>
          <Heading size="sm" mt={1}>62% capacity</Heading>
        </Box>
      </VStack>
    </Box>
  )
}
