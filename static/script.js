// Short helper for finding an element by its HTML id.
const getElement = (id) => document.getElementById(id);

function setText(id, value) {
  const element = getElement(id);
  if (element) element.textContent = value;
  else console.error(`Water reminder page is missing #${id}`);
}
// The latest profile and progress values returned by Flask.
let currentData = null;
let nextReminderTime = 0;
let reminderTimer = null;

// Send a request to Flask and return the JSON response.
async function sendRequestToFlask(path, body) {
  const response = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Something went wrong.');
  return data;
}

function updateDashboard(data) {
  // Fill the overview and progress section with values from Flask.
  currentData = data;
  setText('goal', `${Number(data.goal_liters).toFixed(2)} L`);
  setText('goalMl', `${Math.round(data.goal_liters * 1000)} ml · ${data.goal_glasses} glasses`);
  setText('consumed', `${Number(data.consumed_liters).toFixed(2)} L`);
  setText('consumedMl', `${data.water_count * 250} ml`);
  setText('remaining', `${Number(Math.max(0, data.goal_liters - data.consumed_liters)).toFixed(2)} L`);
  setText('remainingMl', `${data.remaining_glasses * 250} ml`);
  setText('percent', `${data.progress}%`);
  setText('ringPercent', `${data.progress}%`);
  setText('progressLiters', `${Number(data.consumed_liters).toFixed(2)} L`);
  setText('goalInline', `${Number(data.goal_liters).toFixed(2)} L`);
  const bar = getElement('barFill');
  if (bar) {
    bar.style.width = `${data.progress}%`;
  }

  const ring = getElement('ring');
  if (ring) {
    ring.style.background = `conic-gradient(#2787ed ${data.progress * 3.6}deg,#dce8f5 0deg)`;
  }

  setText('activeText', data.active ? 'Active' : 'Paused');
  const toggle = getElement('toggle');
  if (toggle) {
    toggle.classList.toggle('on', data.active);
    toggle.setAttribute('aria-pressed', String(data.active));
  }
  setText('intervalDisplay', `${data.interval_minutes} minutes`);
  setText('intervalText', data.interval_minutes);
  setText('lastReminder', data.last_reminder || 'Not yet today');
  if (data.active) {
    scheduleReminder();
  } else {
    clearInterval(reminderTimer);
  }
}

function scheduleReminder() {
  // Remove the old timer before starting a new one.
  clearInterval(reminderTimer);
  if (currentData.water_count >= currentData.goal_glasses) {
    currentData.active = false;
    setText('activeText', 'Paused');
    const toggle = getElement('toggle');
    if (toggle) {
      toggle.classList.remove('on');
      toggle.setAttribute('aria-pressed', 'false');
    }
    return;
  }
  nextReminderTime = Date.now() + Number(currentData.interval_minutes) * 60000;
  reminderTimer = setInterval(async () => {
    if (!currentData?.active) return;
    const remaining = Math.max(0, Math.ceil((nextReminderTime - Date.now()) / 60000));
    setText('nextReminder', remaining ? `In ${remaining} min` : 'Due now');
    if (Date.now() >= nextReminderTime) {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Time to drink water 💧', { body: 'You need to drink some water now!' });
      }
      playBeep(currentData.sound);
      sendRequestToFlask('/api/reminded', {})
        .then(updateDashboard)
        .catch(() => {});
      nextReminderTime = Date.now() + Number(currentData.interval_minutes) * 60000;
    }
  }, 1000);
}

function playBeep(choice) {
  const frequencies = { '1': 1000, '2': 2000, '3': 3000 };
  try {
    const context = new AudioContext();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.frequency.value = frequencies[choice] || frequencies['1'];
    gain.gain.value = 0.08;
    oscillator.connect(gain); gain.connect(context.destination);
    oscillator.start(); oscillator.stop(context.currentTime + 0.5);
    oscillator.onended = () => context.close();
  } catch (_) { /* Browser audio may be unavailable or blocked. */ }
}

async function addWater(amount) {
  try {
    const data = await sendRequestToFlask('/api/water', { amount_ml: Number(amount) });
    updateDashboard(data);
    showToast(`${amount} ml added. Nice work!`);
    setTimeout(() => getElement('toast')?.classList.remove('visible'), 2200);
  } catch (error) {
    showToast(error.message, true);
  }
}

function showToast(message, isError = false) {
  const toast = getElement('toast');
  if (!toast) {
    console.error('Water reminder page is missing #toast');
    return;
  }
  toast.textContent = message;
  toast.style.color = isError ? '#bd3945' : '';
  toast.classList.add('visible');
}

// Quick-add buttons already contain their amount in data-amount.
document.querySelectorAll('[data-amount]').forEach((button) => {
  button.addEventListener('click', () => addWater(button.dataset.amount));
});

getElement('addButton').addEventListener('click', () => {
  const amount = Number(getElement('amount').value);
  const amountIsValid = Number.isInteger(amount)
    && amount >= 250
    && amount <= 5000
    && amount % 250 === 0;

  if (!amountIsValid) {
    showToast('Enter an amount in 250 ml steps, from 250 to 5000 ml.', true);
    return;
  }

  addWater(amount);
});

getElement('toggle').addEventListener('click', async () => {
  try {
    const updatedData = await sendRequestToFlask('/api/reminder', { active: !currentData.active });
    updateDashboard(updatedData);
  } catch (error) {
    showToast(error.message, true);
  }
});

getElement('missedButton').addEventListener('click', async () => {
  try {
    const updatedData = await sendRequestToFlask('/api/missed', {});
    updateDashboard(updatedData);
    showToast('Reminder marked as missed.');
  } catch (error) {
    showToast(error.message, true);
  }
});

getElement('notifyButton').addEventListener('click', async () => {
  if (!('Notification' in window)) {
    showToast('This browser does not support notifications.', true);
    return;
  }

  const permission = await Notification.requestPermission();
  const permissionGranted = permission === 'granted';
  const message = permissionGranted
    ? 'Notifications enabled while this page is open.'
    : 'Notification permission was not granted.';
  showToast(message, !permissionGranted);
});

getElement('setupOpen').addEventListener('click', () => {
  getElement('setupDialog').showModal();
});
getElement('closeDialog').addEventListener('click', () => {
  getElement('setupDialog').close();
});

getElement('setupForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  getElement('setupError').textContent = '';
  try {
    const updatedData = await sendRequestToFlask('/api/setup', payload);
    updateDashboard(updatedData);
    getElement('setupDialog').close();
  } catch (error) {
    getElement('setupError').textContent = error instanceof TypeError
      ? 'The page script and layout were out of sync. Refresh the page and try again.'
      : error.message;
  }
});

// Load the saved dashboard values when the page first opens.
(async () => {
  try {
    const data = await sendRequestToFlask('/api/state');
    updateDashboard(data);
    if (!data.weight) {
      getElement('setupDialog').showModal();
    }
  } catch (error) {
    showToast(error.message, true);
  }
})();
