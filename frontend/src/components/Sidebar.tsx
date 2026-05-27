import { Box, VStack, HStack, Avatar, Heading, Text, Badge, Button, Divider } from '@chakra-ui/react'
import { FiShield, FiActivity, FiBarChart2, FiSettings } from 'react-icons/fi'

const navItems = [
  { label: 'Dashboard', icon: FiBarChart2 },
  { label: 'Scans', icon: FiActivity },
  { label: 'Threats', icon: FiShield },
  { label: 'Settings', icon: FiSettings },
]

export default function Sidebar() {
  return (
    <Box
      minW={{ base: '100%', lg: '280px' }}
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
              <Text fontSize="sm" color="gray.400">
                System Health
              </Text>
              <Heading size="sm">Operational</Heading>
            </Box>
            <Badge colorScheme="green" variant="subtle" px={3} py={1} borderRadius="full">
              Stable
            </Badge>
          </HStack>
        </Box>

        <Divider borderColor="whiteAlpha.100" />

        <VStack align="stretch" spacing={3} w="full">
          {navItems.map((item) => (
            <Button
              key={item.label}
              variant="ghost"
              justifyContent="flex-start"
              w="full"
              gap={3}
              leftIcon={<item.icon />}
              colorScheme="brand"
              borderRadius="2xl"
              transition="background 0.2s, transform 0.2s"
              _hover={{ bg: 'whiteAlpha.100', transform: 'translateX(2px)' }}
            >
              {item.label}
            </Button>
          ))}
        </VStack>

        <Box mt="auto" bg="whiteAlpha.50" borderRadius="2xl" p={4} w="full">
          <Text fontSize="sm" color="gray.400" mb={2}>
            Workload
          </Text>
          <Heading size="md">62% capacity</Heading>
        </Box>
      </VStack>
    </Box>
  )
}
