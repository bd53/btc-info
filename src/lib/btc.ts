import { Response, Transaction } from '../types';
import { formatDate, generateHash, satoshisToBTC } from '../utils';

const transform = (tx: NonNullable<Response['txs']>[number], price: number): Transaction => {
  const { hash: fullHash, out, time, size } = tx;
  const shortHash = generateHash(fullHash);
  const satoshis = out.reduce((sum, { value }) => sum + value, 0);
  const valueBTC = satoshisToBTC(satoshis);
  return { fullHash, shortHash, value: `${valueBTC} BTC`, valueUSD: valueBTC * price, time: formatDate(time), size };
};

export const fetchBitcoinPrice = async (): Promise<number> => {
  try {
    const response = await fetch('https://blockchain.info/ticker');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data: Record<string, { last: number }> = await response.json();
    const USD = data['USD'];
    if (!USD || typeof USD.last !== 'number') throw new Error('Invalid price structure');
    return USD.last;
  } catch (err) {
    console.error('Failed to fetch Bitcoin price:', err);
    return 0;
  }
};

export const fetchBitcoinTransactions = async (price: number): Promise<Transaction[]> => {
  try {
    const response = await fetch('https://blockchain.info/unconfirmed-transactions?format=json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data: Response = await response.json();
    const txs = data.txs ?? [];
    if (txs.length === 0) return [];
    return txs.slice(0, 11).map(tx => transform(tx, price));
  } catch (err) {
    console.error('Failed to fetch Bitcoin transactions:', err);
    return [];
  }
};
