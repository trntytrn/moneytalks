let ENDPOINT_URL = "http://localhost:3000";

document.getElementById('fetch-data-btn').addEventListener('click', fetchData);

function fetchData() {
    fetch(ENDPOINT_URL + "/data") // Replace with your backend API URL
        .then(response => response.json())
        .then(data => {
            document.getElementById('api-result').innerText = JSON.stringify(data, null, 2);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('api-result').innerText = 'Error fetching data';
        });
}