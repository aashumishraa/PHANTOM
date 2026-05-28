import { useEffect, useRef, useState } from 'react'
import {
  Box, Text, Badge, HStack, VStack, Flex, Spinner,
  IconButton, Tooltip
} from '@chakra-ui/react'
import { CloseIcon } from '@chakra-ui/icons'

export type ScanTerminalProps = {
  scanId: string
  targetUrl: string
  apiBase: string
  onScanComplete: (scanId: string) => void
  onClose: () => void
}

export default function ScanTerminal({ scanId, targetUrl, apiBase, onScanComplete, onClose }: ScanTerminalProps) {
  const [lines, setLines] = useState<string[]>([])
  const [status, setStatus] = useState<'connecting' | 'running' | 'completed' | 'failed' | 'disconnected'>('connecting')
  const bottomRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const wsBase = apiBase.replace(/^http/, 'ws')
    const ws = new WebSocket(`${wsBase}/ws/stream/${scanId}`)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('running')
      setLines(['[PHANTOM] Connecting to scan stream...'])
    }

    ws.onmessage = (event) => {
      const msg: string = event.data
      setLines(prev => [...prev, msg])

      if (msg.includes('✅ Scan completed')) {
        setStatus('completed')
        onScanComplete(scanId)
      } else if (msg.includes('❌ Scan failed')) {
        setStatus('failed')
      }
    }

    ws.onerror = () => {
      setStatus('disconnected')
      setLines(prev => [...prev, '[ERROR] WebSocket connection lost.'])
    }

    ws.onclose = () => {
      if (status === 'running') setStatus('disconnected')
    }

    return () => {
      ws.close()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  const statusColor = {
    connecting: 'yellow',
    running: 'cyan',
    completed: 'green',
    failed: 'red',
    disconnected: 'orange',
  }[status]

  const getLineColor = (line: string) => {
    if (line.includes('✅') || line.includes('completed')) return 'green.300'
    if (line.includes('❌') || line.includes('failed') || line.includes('ERROR')) return 'red.300'
    if (line.includes('⚠️') || line.includes('MOCK') || line.includes('WARNING')) return 'yellow.300'
    if (line.includes('[ZAP]')) return 'purple.300'
    if (line.includes('[NUCLEI]')) return 'cyan.300'
    if (line.includes('[PHANTOM]')) return 'blue.300'
    if (line.includes('🎯') || line.includes('⚡')) return 'orange.300'
    return 'gray.300'
  }

  return (
    <Box
      bg="gray.900"
      border="1px solid"
      borderColor="whiteAlpha.200"
      borderRadius="2xl"
      overflow="hidden"
      boxShadow="2xl"
    >
      {/* Terminal Header */}
      <Flex
        bg="gray.800"
        px={4}
        py={3}
        align="center"
        justify="space-between"
        borderBottom="1px solid"
        borderColor="whiteAlpha.100"
      >
        <HStack spacing={3}>
          {/* macOS-style dots */}
          <HStack spacing={1.5}>
            <Box w={3} h={3} borderRadius="full" bg="red.400" />
            <Box w={3} h={3} borderRadius="full" bg="yellow.400" />
            <Box w={3} h={3} borderRadius="full" bg="green.400" />
          </HStack>
          <Text color="gray.300" fontFamily="mono" fontSize="sm" fontWeight="bold">
            PHANTOM Terminal
          </Text>
          <Text color="gray.500" fontFamily="mono" fontSize="xs">
            — {targetUrl}
          </Text>
        </HStack>
        <HStack spacing={2}>
          {status === 'running' && <Spinner size="xs" color="cyan.400" />}
          <Badge colorScheme={statusColor} fontSize="xs" px={2} borderRadius="full">
            {status.toUpperCase()}
          </Badge>
          <Tooltip label="Close terminal">
            <IconButton
              aria-label="Close terminal"
              icon={<CloseIcon />}
              size="xs"
              variant="ghost"
              color="gray.400"
              _hover={{ color: 'white' }}
              onClick={onClose}
            />
          </Tooltip>
        </HStack>
      </Flex>

      {/* Terminal Body */}
      <Box
        h="280px"
        overflowY="auto"
        p={4}
        fontFamily="'Courier New', monospace"
        fontSize="xs"
        bg="gray.950"
        sx={{
          '&::-webkit-scrollbar': { width: '4px' },
          '&::-webkit-scrollbar-thumb': { background: 'rgba(255,255,255,0.1)', borderRadius: '2px' },
        }}
      >
        <VStack align="stretch" spacing={0.5}>
          {lines.map((line, i) => (
            <Text key={i} color={getLineColor(line)} whiteSpace="pre-wrap" lineHeight="tall">
              <Text as="span" color="gray.600" mr={2}>{String(i + 1).padStart(3, '0')}</Text>
              {line}
            </Text>
          ))}
          {status === 'connecting' && (
            <HStack>
              <Spinner size="xs" color="cyan.400" />
              <Text color="cyan.400" fontFamily="mono" fontSize="xs">Connecting to scan stream...</Text>
            </HStack>
          )}
          <div ref={bottomRef} />
        </VStack>
      </Box>
    </Box>
  )
}
