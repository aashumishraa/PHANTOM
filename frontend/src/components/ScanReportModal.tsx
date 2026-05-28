import {
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton,
  Box, Text, Badge, HStack, VStack, Flex, Divider, SimpleGrid,
  Accordion, AccordionItem, AccordionButton, AccordionPanel, AccordionIcon,
  Stat, StatLabel, StatNumber, StatHelpText, Progress, Spinner, Tag,
  useColorModeValue, Button
} from '@chakra-ui/react'
import { WarningIcon, CheckCircleIcon, InfoIcon, DownloadIcon } from '@chakra-ui/icons'
import axios from 'axios'
import { useEffect, useState } from 'react'

type Severity = 'critical' | 'high' | 'medium' | 'low' | 'informational'

type NucleiFinding = {
  template_id: string
  name: string
  severity: Severity
  host?: string
  matched_url?: string
  description?: string
  remediation?: string
  cvss_score?: number
  tags?: string[]
  payload_used?: string
  extracted_results?: string[]
}

type ZapFinding = {
  alert: string
  risk: string
  confidence: string
  url: string
  method?: string
  param?: string
  description?: string
  solution?: string
  cweid?: string
}

type Summary = {
  total_findings: number
  by_severity: Record<Severity | string, number>
  overall_risk_score?: number
  risk_level?: string
  top_priority_fixes?: string[]
  tools_run?: string[]
}

type ScanData = {
  meta?: { target?: string; mode?: string; note?: string }
  scan_metadata?: { target_url?: string; duration_seconds?: number; tools_used?: string[] }
  nuclei_findings?: NucleiFinding[]
  zap_findings?: ZapFinding[]
  summary?: Summary
}

const severityColor: Record<string, string> = {
  critical: 'red',
  high: 'orange',
  medium: 'yellow',
  low: 'blue',
  informational: 'gray',
  High: 'orange',
  Medium: 'yellow',
  Low: 'blue',
}

const severityBg: Record<string, string> = {
  critical: 'rgba(239,68,68,0.1)',
  high: 'rgba(249,115,22,0.1)',
  medium: 'rgba(234,179,8,0.1)',
  low: 'rgba(59,130,246,0.1)',
  informational: 'rgba(107,114,128,0.1)',
}

export type ScanReportModalProps = {
  isOpen: boolean
  onClose: () => void
  scanId: string
  targetUrl: string
  apiBase: string
}

export default function ScanReportModal({ isOpen, onClose, scanId, targetUrl, apiBase }: ScanReportModalProps) {
  const [data, setData] = useState<ScanData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pollingCount, setPollingCount] = useState(0)
  const [downloading, setDownloading] = useState(false)

  const cardBg = useColorModeValue('gray.800', 'gray.800')

  const handleDownloadPdf = async () => {
    setDownloading(true)
    try {
      const response = await axios.get(`${apiBase}/api/scan/report/${scanId}`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `PHANTOM_Report_${scanId.slice(0, 8)}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      console.error('PDF download failed', e)
    } finally {
      setDownloading(false)
    }
  }

  useEffect(() => {
    if (!isOpen || !scanId) return
    setData(null)
    setError(null)
    setLoading(true)
    setPollingCount(0)
  }, [isOpen, scanId])

  // Poll status until completed, then fetch results
  useEffect(() => {
    if (!isOpen || !scanId) return

    let cancelled = false

    const poll = async () => {
      try {
        const statusRes = await axios.get(`${apiBase}/api/scan/status/${scanId}`)
        const status = statusRes.data.status
        const resultFile: string | null = statusRes.data.result_file

        if (status === 'completed' && resultFile) {
          // Derive the filename from the result_file path and fetch it via a custom endpoint
          // Since the backend doesn't serve the file directly, fetch results via status endpoint
          // We need to read it from the backend — add a results endpoint or use the known JSON
          // For now, call the backend results endpoint we'll expect
          try {
            const resultsRes = await axios.get(`${apiBase}/api/scan/results/${scanId}`)
            if (!cancelled) {
              setData(resultsRes.data)
              setLoading(false)
            }
          } catch {
            // Results endpoint doesn't exist yet — use a fallback approach
            if (!cancelled) {
              setError('Results endpoint not available. See temp_results folder on server.')
              setLoading(false)
            }
          }
        } else if (status === 'failed') {
          if (!cancelled) {
            setError('Scan failed on the server side.')
            setLoading(false)
          }
        } else {
          // Still running — poll again in 2s
          if (!cancelled) {
            setPollingCount(p => p + 1)
            setTimeout(poll, 2000)
          }
        }
      } catch (e) {
        if (!cancelled) {
          setError('Could not reach backend. Is it running?')
          setLoading(false)
        }
      }
    }

    poll()
    return () => { cancelled = true }
  }, [isOpen, scanId, apiBase])

  const summary = data?.summary
  const nucleiFindings = data?.nuclei_findings ?? []
  const zapFindings = data?.zap_findings ?? []
  const riskScore = summary?.overall_risk_score
  const riskColor = riskScore != null
    ? riskScore >= 9 ? 'red.400' : riskScore >= 7 ? 'orange.400' : riskScore >= 4 ? 'yellow.400' : 'green.400'
    : 'gray.400'

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="5xl" scrollBehavior="inside" isCentered>
      <ModalOverlay bg="blackAlpha.800" backdropFilter="blur(8px)" />
      <ModalContent
        bg="gray.900"
        border="1px solid"
        borderColor="whiteAlpha.200"
        borderRadius="2xl"
        maxH="85vh"
      >
        <ModalHeader>
          <Flex justify="space-between" align="flex-start">
            <Box>
              <HStack spacing={3}>
                <Box w={3} h={3} borderRadius="full" bg={loading ? 'yellow.400' : error ? 'red.400' : 'green.400'} />
                <Text color="white" fontWeight="bold">Scan Report</Text>
                <Badge colorScheme="cyan" fontSize="xs" borderRadius="full" px={2}>
                  {scanId.slice(0, 8)}...
                </Badge>
              </HStack>
              <Text color="gray.400" fontSize="sm" fontWeight="normal" mt={1}>{targetUrl}</Text>
            </Box>
            {data && !loading && !error && (
              <Button
                leftIcon={<DownloadIcon />}
                colorScheme="cyan"
                size="sm"
                mr={8}
                isLoading={downloading}
                loadingText="Generating…"
                onClick={handleDownloadPdf}
                _hover={{ transform: 'translateY(-1px)', boxShadow: '0 4px 20px rgba(34,211,238,0.4)' }}
                transition="all 0.2s"
              >
                Download PDF
              </Button>
            )}
          </Flex>
        </ModalHeader>
        <ModalCloseButton color="gray.400" />

        <ModalBody pb={6}>
          {loading && (
            <VStack spacing={4} py={12}>
              <Spinner size="xl" color="cyan.400" thickness="3px" />
              <Text color="gray.300" fontWeight="medium">
                {pollingCount === 0 ? 'Initiating scan...' : `Waiting for results... (${pollingCount * 2}s)`}
              </Text>
              <Text color="gray.500" fontSize="sm">Polling scan status every 2 seconds</Text>
            </VStack>
          )}

          {error && (
            <VStack spacing={3} py={8}>
              <WarningIcon color="orange.400" boxSize={8} />
              <Text color="orange.300" fontWeight="medium">{error}</Text>
              <Text color="gray.500" fontSize="sm" textAlign="center" maxW="md">
                The backend does not yet expose a <code>/api/scan/results/{'{scanId}'}</code> endpoint.
                Check the <code>Backend/temp_results/</code> folder for the raw JSON file.
              </Text>
            </VStack>
          )}

          {data && !loading && !error && (
            <VStack align="stretch" spacing={5}>
              {/* ── Risk Summary Cards ── */}
              <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
                {(['critical', 'high', 'medium', 'low'] as const).map(sev => (
                  <Box
                    key={sev}
                    bg={severityBg[sev]}
                    border="1px solid"
                    borderColor={`${severityColor[sev]}.800`}
                    borderRadius="xl"
                    p={4}
                  >
                    <Stat>
                      <StatLabel color="gray.400" textTransform="capitalize" fontSize="xs">{sev}</StatLabel>
                      <StatNumber color={`${severityColor[sev]}.400`} fontSize="3xl">
                        {summary?.by_severity?.[sev] ?? 0}
                      </StatNumber>
                      <StatHelpText color="gray.500" fontSize="xs">findings</StatHelpText>
                    </Stat>
                  </Box>
                ))}
              </SimpleGrid>

              {/* ── Overall Risk Score ── */}
              {riskScore != null && (
                <Box bg={cardBg} borderRadius="xl" p={5} border="1px solid" borderColor="whiteAlpha.100">
                  <Flex justify="space-between" align="center" mb={3}>
                    <Text color="gray.200" fontWeight="bold">Overall Risk Score</Text>
                    <Text color={riskColor} fontWeight="black" fontSize="2xl">{riskScore} / 10</Text>
                  </Flex>
                  <Progress
                    value={riskScore * 10}
                    colorScheme={riskScore >= 9 ? 'red' : riskScore >= 7 ? 'orange' : 'yellow'}
                    borderRadius="full"
                    size="sm"
                    bg="whiteAlpha.100"
                  />
                  {summary?.risk_level && (
                    <Badge mt={2} colorScheme={severityColor[summary.risk_level.toLowerCase()] ?? 'red'} fontSize="xs">
                      {summary.risk_level}
                    </Badge>
                  )}
                </Box>
              )}

              {/* ── Top Priority Fixes ── */}
              {summary?.top_priority_fixes && summary.top_priority_fixes.length > 0 && (
                <Box bg={cardBg} borderRadius="xl" p={5} border="1px solid" borderColor="whiteAlpha.100">
                  <HStack mb={3}>
                    <WarningIcon color="red.400" />
                    <Text color="gray.200" fontWeight="bold">Top Priority Fixes</Text>
                  </HStack>
                  <VStack align="stretch" spacing={2}>
                    {summary.top_priority_fixes.map((fix, i) => (
                      <HStack key={i} spacing={3} p={2} bg="whiteAlpha.50" borderRadius="lg">
                        <Badge colorScheme="red" borderRadius="full" minW={6} textAlign="center">{i + 1}</Badge>
                        <Text color="gray.300" fontSize="sm">{fix}</Text>
                      </HStack>
                    ))}
                  </VStack>
                </Box>
              )}

              <Divider borderColor="whiteAlpha.100" />

              {/* ── Nuclei Findings ── */}
              {nucleiFindings.length > 0 && (
                <Box>
                  <HStack mb={3}>
                    <Badge colorScheme="cyan" fontSize="sm" px={2} borderRadius="full">NUCLEI</Badge>
                    <Text color="gray.200" fontWeight="bold">{nucleiFindings.length} Findings</Text>
                  </HStack>
                  <Accordion allowMultiple>
                    {nucleiFindings.map((f, i) => (
                      <AccordionItem
                        key={i}
                        border="1px solid"
                        borderColor="whiteAlpha.100"
                        borderRadius="xl"
                        mb={2}
                        bg={severityBg[f.severity]}
                        overflow="hidden"
                      >
                        <AccordionButton py={3} px={4} _hover={{ bg: 'whiteAlpha.100' }}>
                          <HStack flex={1} spacing={3} textAlign="left">
                            <Badge colorScheme={severityColor[f.severity]} fontSize="xs" minW={16} textAlign="center">
                              {f.severity}
                            </Badge>
                            <Text color="gray.200" fontWeight="semibold" fontSize="sm">{f.name}</Text>
                            {f.cvss_score != null && (
                              <Badge colorScheme="gray" fontSize="xs">CVSS {f.cvss_score}</Badge>
                            )}
                          </HStack>
                          <AccordionIcon color="gray.400" />
                        </AccordionButton>
                        <AccordionPanel pb={4} px={4}>
                          <VStack align="stretch" spacing={3}>
                            {f.matched_url && (
                              <Box>
                                <Text color="gray.500" fontSize="xs" mb={1}>URL</Text>
                                <Text color="cyan.300" fontSize="xs" fontFamily="mono" wordBreak="break-all">{f.matched_url}</Text>
                              </Box>
                            )}
                            {f.description && (
                              <Box>
                                <Text color="gray.500" fontSize="xs" mb={1}>Description</Text>
                                <Text color="gray.300" fontSize="sm">{f.description}</Text>
                              </Box>
                            )}
                            {f.extracted_results && f.extracted_results.length > 0 && (
                              <Box>
                                <Text color="gray.500" fontSize="xs" mb={1}>Extracted Evidence</Text>
                                <Box bg="blackAlpha.400" p={3} borderRadius="lg" fontFamily="mono" fontSize="xs">
                                  {f.extracted_results.map((r, j) => (
                                    <Text key={j} color="green.300">{r}</Text>
                                  ))}
                                </Box>
                              </Box>
                            )}
                            {f.payload_used && (
                              <Box>
                                <Text color="gray.500" fontSize="xs" mb={1}>Payload Used</Text>
                                <Box bg="blackAlpha.400" p={2} borderRadius="lg" fontFamily="mono" fontSize="xs">
                                  <Text color="red.300">{f.payload_used}</Text>
                                </Box>
                              </Box>
                            )}
                            {f.remediation && (
                              <Box>
                                <HStack mb={1}>
                                  <CheckCircleIcon color="green.400" boxSize={3} />
                                  <Text color="gray.500" fontSize="xs">Remediation</Text>
                                </HStack>
                                <Text color="green.300" fontSize="sm">{f.remediation}</Text>
                              </Box>
                            )}
                            {f.tags && f.tags.length > 0 && (
                              <HStack flexWrap="wrap">
                                {f.tags.map(tag => (
                                  <Tag key={tag} size="sm" colorScheme="gray" borderRadius="full">{tag}</Tag>
                                ))}
                              </HStack>
                            )}
                          </VStack>
                        </AccordionPanel>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </Box>
              )}

              {/* ── ZAP Findings ── */}
              {zapFindings.length > 0 && (
                <Box>
                  <HStack mb={3}>
                    <Badge colorScheme="purple" fontSize="sm" px={2} borderRadius="full">OWASP ZAP</Badge>
                    <Text color="gray.200" fontWeight="bold">{zapFindings.length} Findings</Text>
                  </HStack>
                  <Accordion allowMultiple>
                    {zapFindings.map((f, i) => (
                      <AccordionItem
                        key={i}
                        border="1px solid"
                        borderColor="whiteAlpha.100"
                        borderRadius="xl"
                        mb={2}
                        bg={severityBg[f.risk] ?? 'transparent'}
                        overflow="hidden"
                      >
                        <AccordionButton py={3} px={4} _hover={{ bg: 'whiteAlpha.100' }}>
                          <HStack flex={1} spacing={3} textAlign="left">
                            <Badge colorScheme={severityColor[f.risk] ?? 'gray'} fontSize="xs" minW={16} textAlign="center">
                              {f.risk}
                            </Badge>
                            <Text color="gray.200" fontWeight="semibold" fontSize="sm">{f.alert}</Text>
                            {f.cweid && <Badge colorScheme="gray" fontSize="xs">CWE-{f.cweid}</Badge>}
                          </HStack>
                          <AccordionIcon color="gray.400" />
                        </AccordionButton>
                        <AccordionPanel pb={4} px={4}>
                          <VStack align="stretch" spacing={3}>
                            <HStack>
                              <Text color="gray.500" fontSize="xs">Method:</Text>
                              {f.method && <Badge colorScheme="green" fontSize="xs">{f.method}</Badge>}
                              {f.param && <><Text color="gray.500" fontSize="xs">Param:</Text><Badge colorScheme="orange" fontSize="xs">{f.param}</Badge></>}
                              <Text color="gray.500" fontSize="xs">Confidence: {f.confidence}</Text>
                            </HStack>
                            <Box>
                              <Text color="gray.500" fontSize="xs" mb={1}>URL</Text>
                              <Text color="cyan.300" fontSize="xs" fontFamily="mono" wordBreak="break-all">{f.url}</Text>
                            </Box>
                            {f.description && (
                              <Box>
                                <Text color="gray.500" fontSize="xs" mb={1}>Description</Text>
                                <Text color="gray.300" fontSize="sm">{f.description}</Text>
                              </Box>
                            )}
                            {f.solution && (
                              <Box>
                                <HStack mb={1}>
                                  <InfoIcon color="blue.400" boxSize={3} />
                                  <Text color="gray.500" fontSize="xs">Solution</Text>
                                </HStack>
                                <Text color="blue.300" fontSize="sm">{f.solution}</Text>
                              </Box>
                            )}
                          </VStack>
                        </AccordionPanel>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </Box>
              )}

              {nucleiFindings.length === 0 && zapFindings.length === 0 && (
                <VStack py={8} spacing={2}>
                  <CheckCircleIcon color="green.400" boxSize={8} />
                  <Text color="green.300" fontWeight="medium">No vulnerabilities found</Text>
                  <Text color="gray.500" fontSize="sm">The target appears secure based on the scan.</Text>
                </VStack>
              )}
            </VStack>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  )
}
