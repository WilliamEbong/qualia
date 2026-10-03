import type { ButtonHTMLAttributes } from 'react'

/** Native-button variant of shadcn's open-source button primitive; theme lives in CSS. */
export function Button({ className = '', type = 'button', ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button data-slot="button" className={`button ${className}`} type={type} {...props} />
}
