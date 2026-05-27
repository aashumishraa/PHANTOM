import { Box, Button, Heading, HStack, Input, InputGroup, InputLeftElement, Text, useColorModeValue } from '@chakra-ui/react'
import { SearchIcon, AddIcon } from '@chakra-ui/icons'

export type ActionCenterProps = {
  query: string
  onQueryChange: (value: string) => void
  onSubmit: () => void
  isLoading: boolean
}

export default function ActionCenter({ query, onQueryChange, onSubmit, isLoading }: ActionCenterProps) {
  const cardBg = useColorModeValue('whiteAlpha.100', 'whiteAlpha.100')

  return (
    <Box bg={cardBg} borderRadius="3xl" p={5} boxShadow="xl" border="1px solid" borderColor="whiteAlpha.100">
      <Heading size="sm" mb={4} color="gray.100">
        Initiate New Scan
      </Heading>
      <Text color="gray.400" mb={4}>
        Enter a target URL to start a new security scan and see realtime updates.
      </Text>
      <HStack spacing={3} flexWrap="wrap">
        <InputGroup flex={1} minW="260px">
          <InputLeftElement pointerEvents="none" children={<SearchIcon color="gray.400" />} />
          <Input
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="https://target.example"
            bg={useColorModeValue('whiteAlpha.100', 'whiteAlpha.100')}
            color="gray.100"
            border="1px solid"
            borderColor="whiteAlpha.100"
          />
        </InputGroup>
        <Button
          colorScheme="brand"
          leftIcon={<AddIcon />}
          onClick={onSubmit}
          isLoading={isLoading}
          loadingText="Scanning"
          flexShrink={0}
          minW="160px"
          _hover={{ transform: 'translateY(-1px)' }}
          transition="all 0.2s ease"
        >
          Initiate Scan
        </Button>
      </HStack>
    </Box>
  )
}
