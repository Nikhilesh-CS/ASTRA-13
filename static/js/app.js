/**
 * Quantum Astra - QDS Interactive Simulation Controller
 * Accessible, Responsive, and Robust Client-Side Implementation
 * SIH 2026 | Problem Statement SIH26141
 */

// Application State
let isSimulating = false;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize slider value readouts
    updateSliderLabels();

    // Attach listeners to attack scenario radios to ensure styling & keyboard focus
    const radioInputs = document.querySelectorAll('input[name="attack_type"]');
    radioInputs.forEach(radio => {
        radio.addEventListener('change', () => {
            hideError();
        });
    });

    // Note: Per design requirement, we DO NOT auto-run on initial load.
    // The initial state remains "Ready to Simulate" / "Awaiting Execution".
});

/* --------------------------------------------------------------------------
   DISCLOSURE / ACCORDION TOGGLES (ACCESSIBLE)
   -------------------------------------------------------------------------- */
function toggleConceptGuide() {
    const drawer = document.getElementById('conceptGuideDrawer');
    const btn = document.getElementById('toggleConceptsBtn');
    const isExpanded = btn.getAttribute('aria-expanded') === 'true';

    if (isExpanded) {
        drawer.hidden = true;
        btn.setAttribute('aria-expanded', 'false');
    } else {
        drawer.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
    }
}

function toggleAdvancedSettings() {
    const section = document.getElementById('advSettingsSection');
    const btn = document.getElementById('advSettingsToggle');
    const isExpanded = btn.getAttribute('aria-expanded') === 'true';

    if (isExpanded) {
        section.hidden = true;
        btn.setAttribute('aria-expanded', 'false');
    } else {
        section.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
    }
}

function toggleQubitInspector() {
    const container = document.getElementById('qubitGridContainer');
    const btn = document.getElementById('qubitToggleBtn');
    const label = document.getElementById('qubitToggleLabel');
    const isExpanded = btn.getAttribute('aria-expanded') === 'true';

    if (isExpanded) {
        container.hidden = true;
        btn.setAttribute('aria-expanded', 'false');
        label.textContent = 'View Details';
    } else {
        container.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
        label.textContent = 'Hide Details';
    }
}

/* --------------------------------------------------------------------------
   FORM CONTROLS & PRESETS
   -------------------------------------------------------------------------- */
function setPresetMessage(text) {
    const input = document.getElementById('messageInput');
    input.value = text;
    input.focus();
}

function updateSliderLabels() {
    const qubits = document.getElementById('qubitCountSlider').value;
    const noise = document.getElementById('ambientNoiseSlider').value;
    const threshold = document.getElementById('thresholdSlider').value;

    document.getElementById('qubitCountVal').textContent = `${qubits} Qubits`;
    document.getElementById('ambientNoiseVal').textContent = `${noise}%`;
    document.getElementById('thresholdVal').textContent = `${threshold}%`;
}

function getSelectedAttackType() {
    const checkedRadio = document.querySelector('input[name="attack_type"]:checked');
    return checkedRadio ? checkedRadio.value : 'NONE';
}

/* --------------------------------------------------------------------------
   ERROR HANDLING (INLINE NOTIFICATION COMPONENT)
   -------------------------------------------------------------------------- */
function showError(title, message, allowRetry = true) {
    const alertBox = document.getElementById('errorAlert');
    const titleEl = document.getElementById('errorTitle');
    const msgEl = document.getElementById('errorMessage');
    const retryBtn = document.getElementById('errorRetryBtn');

    titleEl.textContent = title;
    msgEl.textContent = message;

    if (allowRetry) {
        retryBtn.hidden = false;
        retryBtn.style.display = 'inline-block';
    } else {
        retryBtn.hidden = true;
        retryBtn.style.display = 'none';
    }

    alertBox.hidden = false;
    alertBox.style.display = 'flex';
    alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function dismissError() {
    const alertBox = document.getElementById('errorAlert');
    alertBox.hidden = true;
    alertBox.style.display = 'none';
}

function hideError() {
    const alertBox = document.getElementById('errorAlert');
    alertBox.hidden = true;
    alertBox.style.display = 'none';
}

/* --------------------------------------------------------------------------
   SIMULATION DISPATCH & RESPONSE HANDLING
   -------------------------------------------------------------------------- */
async function runSimulation() {
    if (isSimulating) return; // Prevent duplicate requests
    isSimulating = true;
    hideError();

    const runBtn = document.getElementById('runSimBtn');
    const runBtnLabel = document.getElementById('runBtnLabel');
    const statusTag = document.getElementById('statusTag');
    const resultsPanel = document.getElementById('resultsSection');

    // UI Loading State
    runBtn.disabled = true;
    runBtn.setAttribute('aria-busy', 'true');
    resultsPanel.setAttribute('aria-busy', 'true');
    runBtnLabel.textContent = 'Running Quantum Simulation...';
    statusTag.textContent = 'Simulating...';
    statusTag.style.color = 'var(--cyan)';

    // Gather and sanitize input values
    const rawMessage = document.getElementById('messageInput').value.trim();
    const message = rawMessage || 'Authorize Critical Transaction #9921';
    const qubitCount = parseInt(document.getElementById('qubitCountSlider').value, 10);
    const ambientNoise = parseFloat(document.getElementById('ambientNoiseSlider').value);
    const threshold = parseFloat(document.getElementById('thresholdSlider').value);
    const attackType = getSelectedAttackType();

    const payload = {
        message: message,
        qubit_count: qubitCount,
        ambient_noise: ambientNoise,
        threshold: threshold,
        attack_type: attackType
    };

    try {
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            let errorMsg = 'Server communication error';
            try {
                const errData = await response.json();
                if (errData && errData.error) {
                    errorMsg = errData.error;
                }
            } catch {
                errorMsg = `Server returned status code ${response.status}`;
            }
            throw new Error(errorMsg);
        }

        const data = await response.json();
        renderResults(data);

        // Auto-scroll on mobile/tablet viewports (< 1024px)
        if (window.innerWidth < 1024) {
            const verdictBanner = document.getElementById('verdictBanner');
            verdictBanner.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

    } catch (err) {
        console.error('Simulation execution failed:', err);
        showError('Simulation Error', err.message || 'Unable to execute quantum simulation.', true);
        statusTag.textContent = 'Execution Failed';
        statusTag.style.color = 'var(--status-threat)';
    } finally {
        runBtn.disabled = false;
        runBtn.removeAttribute('aria-busy');
        resultsPanel.removeAttribute('aria-busy');
        runBtnLabel.textContent = 'Run Quantum Simulation';
        isSimulating = false;
    }
}

/* --------------------------------------------------------------------------
   SAFE DOM RENDERING (NO RAW UNSAFE HTML INJECTIONS)
   -------------------------------------------------------------------------- */
function renderResults(data) {
    const ver = data.verification;
    const metrics = ver.metrics;
    const attack = data.attack_info;

    // 1. Status Tag in Panel Header
    const statusTag = document.getElementById('statusTag');
    if (ver.verdict === 'ACCEPT') {
        statusTag.textContent = 'Verification Passed';
        statusTag.style.color = 'var(--status-safe)';
    } else {
        statusTag.textContent = 'Threat Intercepted';
        statusTag.style.color = 'var(--status-threat)';
    }

    // 2. Hero Verdict Banner
    const banner = document.getElementById('verdictBanner');
    const icon = document.getElementById('verdictIcon');
    const pill = document.getElementById('verdictPill');
    const title = document.getElementById('verdictTitle');
    const subtitle = document.getElementById('verdictSubtitle');
    const chipsContainer = document.getElementById('verdictMetaChips');
    const chipQber = document.getElementById('chipQber');
    const chipThreshold = document.getElementById('chipThreshold');
    const chipErrors = document.getElementById('chipErrors');

    banner.classList.remove('initial', 'accept', 'reject');
    chipsContainer.hidden = false;

    if (ver.verdict === 'ACCEPT') {
        banner.classList.add('accept');
        icon.textContent = '🛡️';
        pill.textContent = 'AUTHENTIC';
        title.textContent = 'SIGNATURE VERIFIED';
        subtitle.textContent = 'Configured verification checks passed. Quantum state fidelity within normal baseline limits.';
    } else {
        banner.classList.add('reject');
        icon.textContent = '🚨';
        pill.textContent = 'BLOCKED';
        title.textContent = `THREAT DETECTED: ${formatThreatName(ver.threat_type)}`;
        subtitle.textContent = ver.reasons && ver.reasons.length > 0 
            ? ver.reasons[0] 
            : 'Quantum state disturbances or signature parameters exceeded configured threshold.';
    }

    chipQber.textContent = `QBER: ${metrics.qber_percent}%`;
    chipThreshold.textContent = `Threshold: ${metrics.threshold_percent}%`;
    chipErrors.textContent = `Errors: ${metrics.errors_detected} / ${metrics.total_qubits}`;

    // 3. Top Metrics Row
    const qberVal = document.getElementById('metricQber');
    const qberLimit = document.getElementById('metricQberThreshold');
    const qberBar = document.getElementById('qberBarFill');
    const speedVal = document.getElementById('metricSpeed');
    const mismatchesVal = document.getElementById('metricMismatches');

    qberVal.textContent = `${metrics.qber_percent}%`;
    qberLimit.textContent = `/ ${metrics.threshold_percent}% cutoff`;
    speedVal.textContent = `${metrics.verification_time_ms} ms`;
    mismatchesVal.textContent = `${metrics.errors_detected} / ${metrics.total_qubits}`;

    const fillPercent = Math.min(100, (metrics.qber_percent / 50.0) * 100);
    qberBar.style.width = `${fillPercent}%`;

    if (metrics.qber_percent > metrics.threshold_percent) {
        qberBar.style.background = 'var(--status-threat)';
        qberVal.style.color = 'var(--status-threat)';
    } else {
        qberBar.style.background = 'var(--status-safe)';
        qberVal.style.color = 'var(--status-safe)';
    }

    // 4. Plain-English Explanation Box (Built with safe DOM manipulation)
    const explanationEl = document.getElementById('plainExplanationText');
    explanationEl.textContent = ''; // Clear

    const scenarioLine = document.createElement('div');
    const scenarioLabel = document.createElement('strong');
    scenarioLabel.textContent = 'Scenario: ';
    scenarioLine.appendChild(scenarioLabel);
    scenarioLine.appendChild(document.createTextNode(attack.attack_name));

    const whatLine = document.createElement('div');
    whatLine.style.marginTop = '4px';
    const whatLabel = document.createElement('strong');
    whatLabel.textContent = 'Physical Behavior: ';
    whatLine.appendChild(whatLabel);
    whatLine.appendChild(document.createTextNode(attack.plain_explanation));

    const whyLine = document.createElement('div');
    whyLine.style.marginTop = '4px';
    const whyLabel = document.createElement('strong');
    whyLabel.textContent = 'Verdict Rationale: ';
    whyLine.appendChild(whyLabel);
    const whyText = ver.verdict === 'ACCEPT'
        ? 'Teleported quantum states matched expected verification states within safe baseline limits.'
        : 'Physical wave function collapse and cryptographic freshness checks proved the presence of an active security threat.';
    whyLine.appendChild(document.createTextNode(whyText));

    explanationEl.appendChild(scenarioLine);
    explanationEl.appendChild(whatLine);
    explanationEl.appendChild(whyLine);

    // 5. Security Verification Pipeline (Checklist)
    const checklistContainer = document.getElementById('checklistContainer');
    checklistContainer.textContent = ''; // Clear

    ver.checks.forEach(check => {
        const isPass = check.status && check.status.includes('PASSED');
        const item = document.createElement('div');
        item.className = 'check-item ' + (isPass ? 'passed' : 'failed');

        const badge = document.createElement('span');
        badge.className = 'check-badge';
        badge.setAttribute('aria-hidden', 'true');
        badge.textContent = isPass ? '✅' : '❌';

        const info = document.createElement('div');
        info.className = 'check-info';

        const title = document.createElement('strong');
        title.textContent = check.step;

        const detail = document.createElement('p');
        detail.textContent = check.detail;

        info.appendChild(title);
        info.appendChild(detail);
        item.appendChild(badge);
        item.appendChild(info);
        checklistContainer.appendChild(item);
    });

    // 6. Individual Qubit Measurement Grid (Technical Section)
    const summaryText = document.getElementById('qubitSummaryText');
    const matchedCount = metrics.total_qubits - metrics.errors_detected;
    summaryText.textContent = `${metrics.total_qubits} Qubits Tested: ${matchedCount} Matched, ${metrics.errors_detected} Mismatched.`;

    const qubitGrid = document.getElementById('qubitGrid');
    qubitGrid.textContent = ''; // Clear

    ver.measurement_details.forEach(item => {
        const chip = document.createElement('div');
        chip.className = 'qubit-chip ' + (item.match ? 'match' : 'mismatch');
        chip.setAttribute('role', 'listitem');

        const qId = document.createElement('span');
        qId.className = 'qubit-id';
        qId.textContent = `#${item.qubit_index}`;

        const qBasis = document.createElement('span');
        qBasis.className = 'qubit-basis';
        qBasis.textContent = `${item.basis}-Basis`;

        const qBits = document.createElement('div');
        qBits.className = 'qubit-bits';

        const expSpan = document.createElement('span');
        expSpan.className = 'expected';
        expSpan.textContent = String(item.expected);

        const arrow = document.createElement('span');
        arrow.className = 'arrow';
        arrow.textContent = '➔';

        const measSpan = document.createElement('span');
        measSpan.className = 'measured';
        measSpan.textContent = String(item.measured);

        qBits.appendChild(expSpan);
        qBits.appendChild(arrow);
        qBits.appendChild(measSpan);

        chip.appendChild(qId);
        chip.appendChild(qBasis);
        chip.appendChild(qBits);

        chip.title = `Qubit #${item.qubit_index} measured in ${item.basis}-basis: Expected ${item.expected}, Measured ${item.measured} (${item.match ? 'Match' : 'Mismatch'})`;
        qubitGrid.appendChild(chip);
    });
}

function formatThreatName(type) {
    switch (type) {
        case 'CHANNEL_MANIPULATION_EAVESDROPPING':
            return 'Channel Eavesdropping / MITM';
        case 'FORGERY_PAYLOAD_TAMPERED':
            return 'Document Payload Tampering';
        case 'IMPERSONATION_OR_FORGERY':
            return 'Counterfeit Signature / Impersonation';
        case 'REPLAY_ATTACK':
            return 'Replay Attack (Stale Nonce)';
        default:
            return 'Quantum Security Anomaly';
    }
}
