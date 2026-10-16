import { describe, it, expect, beforeEach } from "vitest";
import { useUiStore } from "./uiStore";

describe("uiStore", () => {
  beforeEach(() => {
    useUiStore.setState({
      selectedTxId: null,
      isPinned: false,
      statusFilter: null,
    });
  });

  it("initializes with default values", () => {
    const state = useUiStore.getState();
    expect(state.selectedTxId).toBeNull();
    expect(state.isPinned).toBe(false);
    expect(state.statusFilter).toBeNull();
  });

  it("updates selectedTxId correctly", () => {
    useUiStore.getState().setSelectedTxId("tx-123");
    expect(useUiStore.getState().selectedTxId).toBe("tx-123");
  });

  it("toggles isPinned flag", () => {
    useUiStore.getState().setIsPinned(true);
    expect(useUiStore.getState().isPinned).toBe(true);
  });
});
