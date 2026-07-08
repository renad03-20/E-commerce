import React, { useState, useEffect } from 'react';
import ProductCard from './ProductCard';

const ProductGrid = () => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/admin/products/')
      .then(res => res.json())
      .then(data => setProducts(data))
      .catch(err => console.error("Error fetching Happy Pet data:", err));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <h2 className="text-3xl font-black text-gray-900 mb-8 tracking-tight">
        Trending in <span className="text-orange-500">Paradise</span> ✨
      </h2>
      
      {/* Responsive Grid Layout */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {products.map(product => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
};

export default ProductGrid;