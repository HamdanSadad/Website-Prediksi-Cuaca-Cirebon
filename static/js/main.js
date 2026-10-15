document.addEventListener('DOMContentLoaded', () => {
    // Set default datetime to current time
    const datetimeInput = document.getElementById('datetime');
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    datetimeInput.value = now.toISOString().slice(0, 16);

    const form = document.getElementById('prediction-form');
    const btnText = document.getElementById('btn-text');
    const btnLoading = document.getElementById('btn-loading');
    const errorMsg = document.getElementById('error-message');
    
    // Initialize Chart
    const ctx = document.getElementById('predictionChart').getContext('2d');
    let predictionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Saat Ini', '6 Jam Kedepan', '24 Jam Kedepan'],
            datasets: [{
                label: 'PM2.5 (µg/m³)',
                data: [null, null, null],
                borderColor: '#0284c7', // Primary color
                backgroundColor: 'rgba(2, 132, 199, 0.1)',
                borderWidth: 3,
                pointBackgroundColor: '#0284c7',
                pointRadius: 6,
                pointHoverRadius: 8,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Konsentrasi PM2.5'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    let currentWeatherData = null;

    async function fetchWeatherData(dtValue) {
        try {
            const response = await fetch(`/api/weather-auto?datetime=${encodeURIComponent(dtValue)}`);
            const result = await response.json();

            if (result.status === 'success') {
                currentWeatherData = result;
                return true;
            } else {
                showError(`Gagal mengambil data cuaca: ${result.message}`);
                return false;
            }
        } catch (error) {
            console.error('Error fetching weather:', error);
            showError('Tidak dapat terhubung ke server untuk mengambil data otomatis.');
            return false;
        }
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const dtValue = document.getElementById('datetime').value;
        if (!dtValue) return;
        
        errorMsg.classList.add('hidden');
        btnText.classList.add('hidden');
        btnLoading.classList.remove('hidden');
        document.getElementById('btn-predict').disabled = true;
        
        // 1. Fetch weather data first
        const success = await fetchWeatherData(dtValue);
        
        if (!success) {
            btnText.classList.remove('hidden');
            btnLoading.classList.add('hidden');
            document.getElementById('btn-predict').disabled = false;
            return;
        }
        
        // 2. Prepare prediction payload
        const formData = {
            datetime: dtValue,
            pm25: currentWeatherData.pm25 || 0,
            suhuC: currentWeatherData.suhuC,
            kelembapan: currentWeatherData.kelembapan,
            curahhujan: currentWeatherData.curahhujanmm,
            angin: currentWeatherData.anginkmh
        };

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.status === 'success') {
                // Populate Saat Ini Card (in Hero Section)
                const valHero = document.getElementById('current-pm-value');
                const badgeHero = document.getElementById('current-badge');
                if (valHero) {
                    valHero.textContent = result.pm25_current;
                    badgeHero.textContent = result.category_current;
                    badgeHero.className = `badge ${result.category_class_current}`;
                    document.getElementById('current-time').textContent = `Tercatat pada: ${result.timestamp}`;
                }
                
                // Populate Saat Ini Card (in Results Grid)
                const valCurrent = document.getElementById('val-current');
                const badgeCurrent = document.getElementById('badge-current');
                if (valCurrent) {
                    valCurrent.textContent = result.pm25_current;
                    badgeCurrent.textContent = result.category_current;
                    badgeCurrent.className = `badge ${result.category_class_current}`;
                    document.getElementById('note-current').textContent = `Tercatat pada: ${result.timestamp}`;
                }

                updateUI(result);
            } else {
                showError(result.message || 'Terjadi kesalahan saat memprediksi');
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Tidak dapat terhubung ke server');
        } finally {
            // Restore button state
            btnText.classList.remove('hidden');
            btnLoading.classList.add('hidden');
            document.getElementById('btn-predict').disabled = false;
        }
    });

    function showError(message) {
        errorMsg.textContent = message;
        errorMsg.classList.remove('hidden');
    }

    function updateUI(data) {
        // Update Current Status Card
        document.getElementById('current-pm-value').textContent = data.pm25_current;
        document.getElementById('current-time').textContent = 'Waktu Prediksi: ' + data.timestamp;
        
        const currentBadge = document.getElementById('current-badge');
        currentBadge.textContent = data.category_current;
        currentBadge.className = 'badge ' + data.category_class_current;

        // Update t+6 Card
        const cardT6 = document.getElementById('card-t6');
        cardT6.classList.remove('fade-in');
        void cardT6.offsetWidth; // trigger reflow
        
        document.getElementById('t6-value').textContent = data.pm25_t6;
        const t6Badge = document.getElementById('t6-badge');
        t6Badge.textContent = data.category_t6;
        t6Badge.className = 'badge ' + data.category_class_t6;
        document.getElementById('t6-recommendation').textContent = getRecommendation(data.category_class_t6);
        cardT6.classList.add('fade-in');

        // Update t+24 Card
        const cardT24 = document.getElementById('card-t24');
        cardT24.classList.remove('fade-in');
        void cardT24.offsetWidth; // trigger reflow
        
        document.getElementById('t24-value').textContent = data.pm25_t24;
        const t24Badge = document.getElementById('t24-badge');
        t24Badge.textContent = data.category_t24;
        t24Badge.className = 'badge ' + data.category_class_t24;
        document.getElementById('t24-recommendation').textContent = getRecommendation(data.category_class_t24);
        cardT24.classList.add('fade-in');

        // Update Chart
        predictionChart.data.datasets[0].data = [data.pm25_current, data.pm25_t6, data.pm25_t24];
        predictionChart.update();
    }

    function getRecommendation(categoryClass) {
        switch(categoryClass) {
            case 'good':
                return 'Kualitas udara sangat baik. Ideal untuk aktivitas luar ruangan.';
            case 'moderate':
                return 'Kualitas udara dapat diterima. Kelompok sensitif sebaiknya mengurangi aktivitas fisik berat.';
            case 'unhealthy':
                return 'Kualitas udara tidak sehat. Disarankan menggunakan masker saat keluar ruangan.';
            case 'very-unhealthy':
                return 'Sangat tidak sehat. Hindari seluruh aktivitas fisik di luar ruangan.';
            case 'hazardous':
                return 'Berbahaya! Tetap di dalam ruangan dan tutup jendela/pintu.';
            default:
                return '-';
        }
    }
});
