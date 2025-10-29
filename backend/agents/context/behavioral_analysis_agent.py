"""Behavioral Analysis Agent - Real-time behavioral biometrics and duress detection."""

from typing import Dict
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class BehavioralAnalysisAgent(AegisBaseAgent):
    """Analyzes user behavior patterns and detects duress signals."""
    
    def __init__(self):
        config = AgentConfig.behavioral_analysis_config()
        super().__init__("behavioral_analysis_agent", config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Analyze behavioral patterns and detect duress using AI reasoning."""
        
        session_data = input_data.get('session_data', {})
        device_fingerprint = input_data.get('device_fingerprint')
        session_id = input_data.get('session_id')
        
        self.logger.info(
            "Analyzing behavioral patterns with AI",
            device_fingerprint=device_fingerprint
        )
        
        # Invoke ML model for behavioral analysis
        behavioral_score = await self.invoke_tool('BehavioralAnalysisTool', {
            'typing_patterns': session_data.get('typing_patterns', []),
            'mouse_movements': session_data.get('mouse_movements', []),
            'navigation_patterns': session_data.get('navigation', []),
            'device_fingerprint': device_fingerprint,
            'session_duration': session_data.get('session_duration', 0)
        })
        
        # Detect duress signals (keep rule-based detection)
        duress_signals = self._detect_duress_signals(session_data, behavioral_score)
        
        # Use AI to analyze behavioral risk
        analysis_prompt = """Analyze this behavioral data for fraud and duress indicators:

Behavioral Biometrics:
{behavioral_summary}

Duress Signals Detected:
{duress_summary}

Session Context:
{session_summary}

Based on this evidence, identify all behavioral fraud risk factors. Consider:
- Active phone calls during transactions (CRITICAL - indicates potential coaching by fraudster)
- Typing hesitation and anomalies
- Copy-paste behavior (being fed information)
- Device risk factors
- Navigation anomalies

For each risk factor:
1. Name the risk factor (e.g., "ACTIVE_CALL_DETECTED", "TYPING_HESITATION_ANOMALY")
2. Assign a severity level: LOW, MEDIUM, HIGH, or CRITICAL
3. Assign a numerical weight (0-350 points, with active calls being highest)
4. Provide a brief explanation

Return your response as JSON with this structure:
{{
    "risk_factors": [
        {{
            "factor": "RISK_FACTOR_NAME",
            "severity": "CRITICAL",
            "weight": 350,
            "details": "Explanation of behavioral risk"
        }}
    ],
    "overall_assessment": "Brief summary of behavioral analysis",
    "confidence": 0.92
}}""".format(
            behavioral_summary=self._summarize_behavioral_score(behavioral_score),
            duress_summary=self._summarize_duress_signals(duress_signals),
            session_summary=self._summarize_session_data(session_data)
        )
        
        # Get AI analysis
        ai_analysis = await self.reason_with_bedrock(
            prompt=analysis_prompt,
            context={'behavioral_score': behavioral_score, 'duress': duress_signals, 'session': session_data}
        )
        
        # Extract risk factors from AI response
        risk_factors = ai_analysis.get('risk_factors', [])
        
        # Fallback to rule-based if AI fails
        if not risk_factors or ai_analysis.get('fallback'):
            self.logger.warning("AI analysis failed, using rule-based fallback")
            risk_factors = self._assess_behavioral_risk(duress_signals, behavioral_score)
            overall_assessment = "Rule-based analysis (AI unavailable)"
            confidence = 0.5
        else:
            overall_assessment = ai_analysis.get('overall_assessment', '')
            confidence = ai_analysis.get('confidence', 0.7)
        
        result = {
            'agent': 'behavioral_analysis',
            'anomaly_score': behavioral_score.get('score', 0),
            'duress_detected': duress_signals.get('active_call') or duress_signals.get('high_hesitation'),
            'duress_signals': duress_signals,
            'risk_factors': risk_factors,
            'risk_score_contribution': sum(rf.get('weight', 0) for rf in risk_factors),
            'ai_assessment': overall_assessment,
            'confidence': confidence,
            'reasoning_source': 'ai' if not ai_analysis.get('fallback') else 'rules'
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:behavioral_analysis',
                result,
                ttl=self.config.session_ttl
            )

        return result
    
    def _detect_duress_signals(self, session_data: Dict, behavioral_score: Dict) -> Dict:
        """Detect signals indicating customer duress."""
        
        signals = {}
        
        # Active phone call during transaction (CRITICAL INDICATOR)
        signals['active_call'] = session_data.get('active_call', False)
        
        # Typing hesitation
        typing_anomaly = behavioral_score.get('typing_anomaly', 0)
        signals['high_hesitation'] = typing_anomaly > 0.7
        
        # Copy-paste behavior (being fed information)
        signals['copy_paste_detected'] = session_data.get('copy_paste_detected', False)
        
        # Multiple authentication failures
        signals['auth_failures'] = session_data.get('authentication_failures', 0) > 2
        
        # Unusual navigation patterns
        signals['navigation_anomaly'] = behavioral_score.get('navigation_anomaly', 0) > 0.6
        
        # Device risk
        signals['device_risk'] = behavioral_score.get('device_risk', 0) > 0.5
        
        return signals
    
    def _assess_behavioral_risk(self, duress_signals: Dict, behavioral_score: Dict) -> list:
        """Assess behavioral risk factors."""
        risk_factors = []
        
        # Active call - CRITICAL
        if duress_signals.get('active_call'):
            risk_factors.append({
                'factor': 'ACTIVE_CALL_DETECTED',
                'severity': 'CRITICAL',
                'weight': 350,
                'details': 'Phone call active during transaction - potential coaching'
            })
        
        # High hesitation
        if duress_signals.get('high_hesitation'):
            risk_factors.append({
                'factor': 'TYPING_HESITATION_ANOMALY',
                'severity': 'HIGH',
                'weight': 200,
                'details': f"Typing anomaly score: {behavioral_score.get('typing_anomaly')}"
            })
        
        # Copy-paste behavior
        if duress_signals.get('copy_paste_detected'):
            risk_factors.append({
                'factor': 'COPY_PASTE_DETECTED',
                'severity': 'MEDIUM',
                'weight': 120,
                'details': 'Customer copy-pasting information - possible coaching'
            })
        
        # Authentication failures
        if duress_signals.get('auth_failures'):
            risk_factors.append({
                'factor': 'MULTIPLE_AUTH_FAILURES',
                'severity': 'MEDIUM',
                'weight': 100,
                'details': 'Multiple authentication attempts'
            })
        
        # Device risk
        if duress_signals.get('device_risk'):
            risk_factors.append({
                'factor': 'DEVICE_RISK',
                'severity': 'MEDIUM',
                'weight': 110,
                'details': 'Unknown or suspicious device'
            })
        
        return risk_factors
    
    def _summarize_behavioral_score(self, behavioral_score: Dict) -> str:
        """Summarize behavioral biometrics for AI prompt."""
        if not behavioral_score:
            return "No behavioral data available"
        
        summary = f"""
- Anomaly Score: {behavioral_score.get('score', 0):.2f}
- Typing Anomaly: {behavioral_score.get('typing_anomaly', 0):.2f}
- Mouse Movement Anomaly: {behavioral_score.get('mouse_anomaly', 0):.2f}
- Navigation Anomaly: {behavioral_score.get('navigation_anomaly', 0):.2f}
- Device Risk: {behavioral_score.get('device_risk', 0):.2f}
"""
        return summary.strip()
    
    def _summarize_duress_signals(self, duress_signals: Dict) -> str:
        """Summarize detected duress signals for AI prompt."""
        if not duress_signals:
            return "No duress signals detected"
        
        active_signals = [key for key, value in duress_signals.items() if value]
        
        if not active_signals:
            return "No duress signals detected"
        
        summary = "Active Duress Indicators:\n"
        for signal in active_signals:
            summary += f"- {signal.replace('_', ' ').title()}\n"
        
        return summary.strip()
    
    def _summarize_session_data(self, session_data: Dict) -> str:
        """Summarize session context for AI prompt."""
        if not session_data:
            return "No session data available"
        
        summary = f"""
- Session Duration: {session_data.get('session_duration', 0)} seconds
- Active Call: {'Yes' if session_data.get('active_call') else 'No'}
- Copy/Paste Events: {session_data.get('copy_paste_detected', False)}
- Authentication Failures: {session_data.get('authentication_failures', 0)}
- Device Fingerprint Available: {'Yes' if session_data.get('device_fingerprint') else 'No'}
"""
        return summary.strip()



