export interface Transaction {
  fullHash: string;
  shortHash: string;
  value: string;
  time: string;
  valueUSD: number;
  size: number;
}

export interface Response {
  txs?: {
    hash: string;
    time: number;
    size: number;
    inputs: any[];
    out: { value: number }[];
  }[];
}

export const Datetime: Intl.DateTimeFormatOptions = {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
};