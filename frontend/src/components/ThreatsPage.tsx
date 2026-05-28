import {
  Box, Heading, Text, VStack, HStack, Badge, Flex, Divider,
  SimpleGrid, Progress, Stat, StatLabel, StatNumber, StatHelpText,
  Accordion, AccordionItem, AccordionButton, AccordionPanel, AccordionIcon,
  Tag, List, ListItem, ListIcon
} from '@chakra-ui/react'
import { WarningIcon, CheckCircleIcon, TimeIcon } from '@chakra-ui/icons'

type ThreatItem = {
  id: string
  name: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  target: string
  description: string
  cve?: string
  remediation: string
  detectedAt: string
}

const MOCK_THREATS: ThreatItem[] = [
  {
    id: 'T-001',
    name: 'SQL Injection via Login Form',
    severity: 'critical',
    target: 'http://www.badstore.net/cgi-bin/badstore.cgi',
    description: 'Authentication bypass using SQL injection. The login form is vulnerable to OR 1=1 payloads, allowing attackers to log in as any user including admin.',
    cve: 'CWE-89',
    remediation: 'Use parameterized queries and prepared statements. Never concatenate user input into SQL.',
    detectedAt: '2026-05-28 23:54',
  },
  {
    id: 'T-002',
    name: 'OS Command Injection — Order Tracking',
    severity: 'critical',
    target: 'http://www.badstore.net/cgi-bin/badstore.cgi?action=trackinput',
    description: 'Server-side command injection via the order tracking input field. Appending shell commands executes them on the underlying OS as www-data.',
    cve: 'CWE-78',
    remediation: 'Never pass user input to shell commands. Implement strict allowlist input validation.',
    detectedAt: '2026-05-28 23:54',
  },
  {
    id: 'T-003',
    name: 'Credit Card Data in Cleartext',
    severity: 'critical',
    target: 'http://www.badstore.net/cgi-bin/badstore.cgi?action=viewcart',
    description: 'Full PAN (card numbers), expiry dates, and CVVs stored and transmitted in plaintext. Critical PCI-DSS violation.',
    cve: 'CWE-312',
    remediation: 'Encrypt all PAN data at rest using AES-256. Tokenize card data. Implement HTTPS end-to-end.',
    detectedAt: '2026-05-28 23:54',
  },
  {
    id: 'T-004',
    name: 'Reflected Cross-Site Scripting',
    severity: 'high',
    target: 'http://testphp.vulnweb.com/search.php',
    description: 'Reflected XSS in the search parameter. Attacker can inject malicious JavaScript executed in victim browsers.',
    cve: 'CWE-79',
    remediation: 'HTML-encode all user-supplied output. Implement a strict Content Security Policy header.',
    detectedAt: '2026-05-27 18:23',
  },
  {
    id: 'T-005',
    name: 'Exposed .git Configuration',
    severity: 'high',
    target: 'http://testphp.vulnweb.com/.git/config',
    description: 'Git configuration file is publicly accessible. Exposes repository metadata, remote URLs, and branch names.',
    cve: 'CWE-538',
    remediation: 'Block access to .git/ directories via web server configuration (Nginx/Apache deny rules).',
    detectedAt: '2026-05-27 17:11',
  },
  {
    id: 'T-006',
    name: 'Missing HTTP Security Headers',
    severity: 'medium',
    target: 'Multiple targets',
    description: 'Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options, Content-Security-Policy, and Referrer-Policy headers are absent.',
    remediation: 'Add all OWASP-recommended security headers in your web server or application middleware.',
    detectedAt: '2026-05-27 15:47',
  },
  {
    id: 'T-007',
    name: 'Session Cookie Without Secure Flag',
    severity: 'low',
    target: 'http://www.badstore.net/cgi-bin/badstore.cgi',
    description: 'Session cookie is transmitted without the Secure flag, allowing interception over unencrypted HTTP connections.',
    cve: 'CWE-614',
    remediation: 'Set the Secure and HttpOnly flags on all session cookies.',
    detectedAt: '2026-05-28 23:54',
  },
]

const severityColor: Record<string, string> = {
  critical: 'red',
  high: 'orange',
  medium: 'yellow',
  low: 'blue',
}

const severityBg: Record<string, string> = {
  critical: 'rgba(239,68,68,0.07)',
  high: 'rgba(249,115,22,0.07)',
  medium: 'rgba(234,179,8,0.07)',
  low: 'rgba(59,130,246,0.07)',
}

export default function ThreatsPage() {
  const bySeverity = {
    critical: MOCK_THREATS.filter(t => t.severity === 'critical').length,
    high: MOCK_THREATS.filter(t => t.severity === 'high').length,
    medium: MOCK_THREATS.filter(t => t.severity === 'medium').length,
    low: MOCK_THREATS.filter(t => t.severity === 'low').length,
  }

  return (
    <VStack align="stretch" spacing={6}>
      {/* Header */}
      <Box bg="gray.800" borderRadius="3xl" p={6} boxShadow="2xl" border="1px solid" borderColor="whiteAlpha.100">
        <Flex justify="space-between" align="center">
          <Box>
            <Text color="red.400" fontWeight="bold" textTransform="uppercase" letterSpacing="widest" fontSize="xs">Active Intelligence</Text>
            <Heading size="lg" color="white">Threat Registry</Heading>
            <Text color="gray.400" mt={1} fontSize="sm">All detected vulnerabilities across scanned targets, ranked by severity.</Text>
          </Box>
          <Badge colorScheme="red" fontSize="sm" px={3} py={1} borderRadius="full">
            {MOCK_THREATS.length} Active Threats
          </Badge>
        </Flex>
      </Box>

      {/* Severity Breakdown */}
      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
        {(['critical', 'high', 'medium', 'low'] as const).map(sev => (
          <Box
            key={sev}
            bg={severityBg[sev]}
            border="1px solid"
            borderColor={`${severityColor[sev]}.800`}
            borderRadius="2xl"
            p={4}
          >
            <Stat>
              <StatLabel color="gray.400" textTransform="capitalize" fontSize="xs">{sev}</StatLabel>
              <StatNumber color={`${severityColor[sev]}.400`} fontSize="3xl">{bySeverity[sev]}</StatNumber>
              <StatHelpText color="gray.500" fontSize="xs">threats</StatHelpText>
            </Stat>
          </Box>
        ))}
      </SimpleGrid>

      {/* Risk Bar */}
      <Box bg="gray.800" borderRadius="2xl" p={5} border="1px solid" borderColor="whiteAlpha.100">
        <Flex justify="space-between" mb={2}>
          <Text color="gray.300" fontWeight="semibold" fontSize="sm">Overall Attack Surface Risk</Text>
          <Badge colorScheme="red">CRITICAL</Badge>
        </Flex>
        <Progress value={87} colorScheme="red" borderRadius="full" size="sm" bg="whiteAlpha.100" />
        <Text color="gray.500" fontSize="xs" mt={2}>Risk Score: 8.7/10 — Immediate remediation required</Text>
      </Box>

      <Divider borderColor="whiteAlpha.100" />

      {/* Threat List */}
      <Accordion allowMultiple>
        {MOCK_THREATS.map(threat => (
          <AccordionItem
            key={threat.id}
            border="1px solid"
            borderColor="whiteAlpha.100"
            borderRadius="xl"
            mb={3}
            bg={severityBg[threat.severity]}
            overflow="hidden"
          >
            <AccordionButton py={4} px={5} _hover={{ bg: 'whiteAlpha.100' }}>
              <HStack flex={1} spacing={3} textAlign="left">
                <WarningIcon color={`${severityColor[threat.severity]}.400`} />
                <Badge colorScheme={severityColor[threat.severity]} fontSize="xs" minW={16} textAlign="center">
                  {threat.severity}
                </Badge>
                <Text color="gray.100" fontWeight="semibold" fontSize="sm">{threat.name}</Text>
                {threat.cve && <Badge colorScheme="gray" fontSize="xs">{threat.cve}</Badge>}
              </HStack>
              <HStack mr={2} spacing={2}>
                <Tag size="sm" colorScheme="gray" borderRadius="full">
                  <TimeIcon mr={1} boxSize={2} />{threat.detectedAt}
                </Tag>
              </HStack>
              <AccordionIcon color="gray.400" />
            </AccordionButton>
            <AccordionPanel pb={5} px={5}>
              <VStack align="stretch" spacing={4}>
                <Box>
                  <Text color="gray.500" fontSize="xs" mb={1}>Target</Text>
                  <Text color="cyan.300" fontFamily="mono" fontSize="xs" wordBreak="break-all">{threat.target}</Text>
                </Box>
                <Box>
                  <Text color="gray.500" fontSize="xs" mb={1}>Description</Text>
                  <Text color="gray.300" fontSize="sm">{threat.description}</Text>
                </Box>
                <Box>
                  <HStack mb={2}>
                    <CheckCircleIcon color="green.400" boxSize={3} />
                    <Text color="gray.500" fontSize="xs">Remediation</Text>
                  </HStack>
                  <Text color="green.300" fontSize="sm">{threat.remediation}</Text>
                </Box>
              </VStack>
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>
    </VStack>
  )
}
