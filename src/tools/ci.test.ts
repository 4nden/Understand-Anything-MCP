import { describe, it, expect, vi, beforeEach } from 'vitest';
import { handleCiCheck, handleValidateGraph } from './ci.js';
import * as licenseService from '../services/license.js';

// Mock the entire license service
vi.mock('../services/license.js', () => ({
  requireTier: vi.fn(),
}));

describe('CI Tools', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('handleCiCheck', () => {
    it('throws when requireTier returns false', async () => {
      (licenseService.requireTier as any).mockResolvedValue(false);
      await expect(handleCiCheck({ pr_diff: '+++ b/test.txt' })).rejects.toThrow('ua_ci_check requires a Team tier license.');
    });

    it('succeeds when requireTier returns true', async () => {
      (licenseService.requireTier as any).mockResolvedValue(true);
      const result = await handleCiCheck({ pr_diff: '+++ b/test.txt' });
      expect(result.content).toBeDefined();
      expect(result.content[0].text).toContain('test.txt');
    });
  });

  describe('handleValidateGraph', () => {
    it('throws when requireTier returns false', async () => {
      (licenseService.requireTier as any).mockResolvedValue(false);
      await expect(handleValidateGraph({ graphData: '{}' })).rejects.toThrow('ua_validate_graph requires a Team tier license.');
    });

    it('succeeds when requireTier returns true', async () => {
      (licenseService.requireTier as any).mockResolvedValue(true);
      const result = await handleValidateGraph({ graphData: '{}' });
      expect(result.content).toBeDefined();
      expect(result.content[0].text).toContain('Graph validated successfully');
    });
  });
});
