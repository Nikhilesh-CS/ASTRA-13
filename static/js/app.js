/**
 * Quantum Astra - QDS Interactive Simulation Controller
 * Handles user inputs, scenario switching, API calls, and visual updates.
 */

let selectedAttackType = 'NONE';

document.addEventListener('DOMContentLoaded', () => {
    updateSliderLabels();
    // Run an initial authentic baseline simulation on page load
    runSimulation();
});

function toggleConceptGuide() {
    const drawer = document.getElementById('conceptGuideDrawer');
    const btn = document.getElementById('toggleConceptsBtn');
    if (drawer.style.display === 'none' || drawer.style.display === '') {
        drawer.style.display = 'block';
        btn.textContent = '❌ Close Concept Guide';
    } else {
        drawer.style.display = 'none';
        btn.textContent = '📖 Quantum Concepts Made Simple';
    }
}

function setPresetMessage(text) {
    document.getElementById('messageInput').value = text;
}

function updateSliderLabels() {
    const qubits = document.getElementById('qubitCountSlider').value;
    const noise = document.getElementById('ambientNoiseSlider').value;
    const threshold = document.getElementById('thresholdSlider').value;

    document.getElementById('qubitCountVal').textContent = `${qubits} Qubits`;
    document.getElementById('ambientNoiseVal').textContent = `${noise}%`;
    document.getElementById('thresholdVal').textContent = `${threshold}%`;
}

function selectAttack(type) {
    selectedAttackType = type;
    document.querySelectorAll('.attack-card').forEach(card => {
        if (card.dataset.type === type) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
}

async function runSimulation() {
    const btn = document.getElementById('runSimBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="btn-icon">⏳</span> Teleporting &amp; Verifying...';
    btn.disabled = true;

    const message = document.getElementById('messageInput').value.trim() || "Authorize Critical Action";
    const qubitCount = parseInt(document.getElementById('qubitCountSlider').value, 10);
    const ambientNoise = parseFloat(document.getElementById('ambientNoiseSlider').value);
    const threshold = parseFloat(document.getElementById('thresholdSlider').value);

    const payload = {
        message: message,
        qubit_count: qubitCount,
        ambient_noise: ambientNoise,
        threshold: threshold,
        attack_type: selectedAttackType
    };

    try {
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Server returned error status ${response.status}`);
        }

        const data = await response.json();
        renderResults(data);

    } catch (err) {
        console.error('Simulation error:', err);
        alert('Simulation failed to execute: ' + err.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function renderResults(data) {
    const ver = data.verification;
    const metrics = ver.metrics;
    const attack = data.attack_info;

    // 1. Update Status Tag
    const statusTag = document.getElementById('statusTag');
    statusTag.textContent = ver.verdict === 'ACCEPT' ? 'Signature Verified' : 'Threat Blocked';
    statusTag.style.color = ver.verdict_color;

    // 2. Update Large Verdict Banner
    const banner = document.getElementById('verdictBanner');
    const icon = document.getElementById('verdictIcon');
    const title = document.getElementById('verdictTitle');
    const subtitle = document.getElementById('verdictSubtitle');

    banner.className = 'verdict-banner ' + (ver.verdict === 'ACCEPT' ? 'accept' : 'reject');

    if (ver.verdict === 'ACCEPT') {
        icon.textContent = '🛡️';
        title.textContent = 'AUTHENTIC SIGNATURE ACCEPTED';
        subtitle.textContent = `All quantum teleportation and classical checks passed. Document integrity guaranteed.`;
    } else {
        icon.textContent = '🚨';
        title.textContent = `THREAT DETECTED: ${formatThreatName(ver.threat_type)}`;
        subtitle.textContent = ver.reasons[0] || 'Signature rejected due to quantum threshold violation.';
    }

    // 3. Update Top Metrics Row
    const qberVal = document.getElementById('metricQber');
    const qberLimit = document.getElementById('metricQberThreshold');
    const qberBar = document.getElementById('qberBarFill');
    const speedVal = document.getElementById('metricSpeed');
    const mismatchVal = document.getElementById('metricMismatches');

    qberVal.textContent = `${metrics.qber_percent}%`;
    qberLimit.textContent = `/ ${metrics.threshold_percent}% limit`;
    speedVal.textContent = `${metrics.verification_time_ms} ms`;
    mismatchVal.textContent = `${metrics.errors_detected} / ${metrics.total_qubits}`;

    // Bar fill & color
    const fillPercent = Math.min(100, (metrics.qber_percent / 50.0) * 100);
    qberBar.style.width = `${fillPercent}%`;
    if (metrics.qber_percent > metrics.threshold_percent) {
        qberBar.style.background = 'var(--red-threat)';
        qberVal.style.color = 'var(--red-threat)';
    } else {
        qberBar.style.background = 'var(--emerald-safe)';
        qberVal.style.color = 'var(--emerald-safe)';
    }

    // 4. Update Checklist Pipeline
    const checklistContainer = document.getElementById('checklistContainer');
    checklistContainer.innerHTML = '';

    ver.checks.forEach(check => {
        const isPass = check.status.includes('PASSED');
        const item = document.createElement('div');
        item.className = 'check-item ' + (isPass ? 'passed' : 'failed');
        item.innerHTML = `
            <span class="check-badge">${isPass ? '✅' : '❌'}</span>
            <div class="check-info">
                <strong>${check.step}</strong>
                <p>${check.detail}</p>
            </div>
        `;
        checklistContainer.appendChild(item);
    });

    // 5. Update Plain-English Summary Box
    const plainBox = document.getElementById('plainExplanationText');
    plainBox.innerHTML = `
        <strong>Scenario:</strong> ${attack.attack_name}<br>
        <strong>What Happened:</strong> ${attack.plain_explanation}<br>
        <strong>Why Detection Succeeded:</strong> ${ver.verdict === 'ACCEPT' 
            ? 'The received quantum states matched Alice’s teleported states within safe baseline limits.' 
            : 'The physical and mathematical laws of quantum mechanics made it impossible for the attacker to disguise their interference.'}
    `;

    // 6. Update Qubit Teleportation Inspector Grid
    const qubitGrid = document.getElementById('qubitGrid');
    const badge = document.getElementById('qubitSummaryBadge');
    badge.textContent = `${metrics.total_qubits} Qubits Tested`;
    qubitGrid.innerHTML = '';

    ver.measurement_details.forEach(item => {
        const chip = document.createElement('div');
        chip.className = 'qubit-chip ' + (item.match ? 'match' : 'mismatch');
        chip.innerHTML = `
            <span class="qubit-id">#${item.qubit_index}</span>
            <span class="qubit-basis">${item.basis}-Basis</span>
            <div class="qubit-bits">
                <span class="expected">${item.expected}</span>
                <span class="arrow">➔</span>
                <span class="measured">${item.measured}</span>
            </div>
        `;
        chip.title = `Qubit #${item.qubit_index} measured in ${item.basis} basis. Expected: ${item.expected}, Measured: ${item.measured} (${item.match ? 'Match' : 'Mismatch'})`;
        qubitGrid.appendChild(chip);
    });
}

function formatThreatName(type) {
    switch (type) {
        case 'CHANNEL_MANIPULATION_EAVESDROPPING':
            return 'Channel Manipulation / Eavesdropping';
        case 'FORGERY_PAYLOAD_TAMPERED':
            return 'Document Payload Tampering';
        case 'IMPERSONATION_OR_FORGERY':
            return 'Counterfeit Signature / Impersonation';
        case 'REPLAY_ATTACK':
            return 'Replay Attack (Stale Nonce/Timestamp)';
        default:
            return 'Security Anomaly';
    }
}
