document.getElementById('search-name').addEventListener('input', function () {
    const searchValue = this.value.toLowerCase();
    const products = document.querySelectorAll('#product-list .col-md-4');
    products.forEach(product => {
        const title = product.querySelector('.card-title').textContent.toLowerCase();
        product.style.display = title.includes(searchValue) ? '' : 'none';
    });
});

document.getElementById('filter-category').addEventListener('change', function () {
    const filterValue = this.value;
    const products = document.querySelectorAll('#product-list .col-md-4');
    products.forEach(product => {
        const category = product.getAttribute('data-category');
        product.style.display = filterValue === '' || category === filterValue ? '' : 'none';
    });
});