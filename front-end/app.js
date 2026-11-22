const API_KEY = "foj1eDDT1CM9fDFC0bYB6wtpner7Ialaof8Ia9I5";
const INVOKE_URL = "https://j9rlyct9kb.execute-api.us-east-1.amazonaws.com/prod";

const apigClient = apigClientFactory.newClient({ apiKey: API_KEY });

function search() {
  // We get what the user typed in the search box
  const q = document.getElementById("search-box").value;

  // Then we call GET /search through the SDK and show the results
  apigClient.searchGet({ q: q }, {}, {})
    .then(function (response) {
      showResults(response.data.results);
    })
    .catch(function (error) {
      console.error(error);
      alert("Search failed. Check the browser console for details.");
    });
}

function showResults(results) {
  const area = document.getElementById("results");
  area.innerHTML = "";

  if (results.length === 0) {
    area.innerHTML = "<p>No photos found.</p>";
    return;
  }

  // We create an image for each photo using the url from LF2
  for (const photo of results) {
    const img = document.createElement("img");
    img.src = photo.url;
    img.title = photo.labels.join(", ");
    area.appendChild(img);
  }
}

function upload() {
  // We get the file the user picked and the custom labels they typed
  const file = document.getElementById("file-input").files[0];
  const labels = document.getElementById("labels-box").value;

  if (!file) {
    alert("Choose a photo first.");
    return;
  }

  fetch(`${INVOKE_URL}/photos/${encodeURIComponent(file.name)}`, {
    method: "PUT",
    headers: {
      "x-api-key": API_KEY,
      "Content-Type": file.type,
      "x-amz-meta-customLabels": labels,
    },
    body: file,
  })
    .then(function (response) {
      if (response.ok) {
        alert("Uploaded! It may take a few seconds to show up in searches.");
      } else {
        alert("Upload failed with status " + response.status);
      }
    });
}
