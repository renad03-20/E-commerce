import React from 'react';
import { useCart } from '../context/CartContext';

const ProductCard = ({ product }) => {
  const { addToCart } = useCart();
  // Grab the price of the first variant, fallback if no variants exist
  const displayPrice = product.variants?.[0]?.price || "0.00";
  
  // Placeholder image mimicking the soft, warm backgrounds
  const placeholderImage = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?q=80&w=500&auto=format&fit=crop";

  return (
    <div className="group relative bg-amber-50/30 rounded-3xl p-4 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 border border-transparent hover:border-orange-100 flex flex-col justify-between">
      <div>
        <div className="relative aspect-square w-full rounded-2xl bg-orange-100/50 overflow-hidden flex items-center justify-center mb-4">
          <img 
            src={placeholderImage} 
            alt={product.title} 
            className="object-cover w-4/5 h-4/5 rounded-xl transition-transform duration-300 group-hover:scale-105"
          />
          <span className="absolute top-3 left-3 bg-white/90 text-orange-700 text-xs font-semibold px-2.5 py-1 rounded-full shadow-sm">
            {product.category_name}
          </span>
        </div>

        <h3 className="text-gray-800 font-bold text-lg leading-tight line-clamp-2 px-1">
          {product.title}
        </h3>
      </div>

      <div className="mt-4 pt-2 border-t border-orange-50 flex items-center justify-between px-1">
        <div>
          <span className="text-xs text-gray-400 block font-medium">Price</span>
          <span className="text-xl font-extrabold text-orange-600">${displayPrice}</span>
        </div>
        
        <button 
          onClick={() => addToCart(product)}
          className="bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl px-4 py-2 text-sm transition-colors shadow-sm shadow-orange-200"
        >
          Add
        </button>
      </div>
    </div>
  );
};

export default ProductCard;