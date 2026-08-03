const searchInput = document.getElementById("searchInput");

if (searchInput) {

    searchInput.addEventListener("keyup", function () {

        const filter = this.value.toLowerCase();
        const rows = document.querySelectorAll("#bookingTable tbody tr");

        rows.forEach(row => {

            row.style.display =
                row.textContent.toLowerCase().includes(filter)
                    ? ""
                    : "none";

        });

    });

}

function printPage() {
    window.print();
}