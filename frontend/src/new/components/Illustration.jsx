import React from "react";

export const assetUrl = (name) => `/illustrations/${name}`;

export function Illustration({ name, alt = "", className = "", decorative = false }) {
  return <img className={className} src={assetUrl(name)} alt={decorative ? "" : alt} aria-hidden={decorative || undefined} />;
}
