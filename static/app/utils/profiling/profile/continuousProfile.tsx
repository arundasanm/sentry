import type {createFrameIndex} from 'sentry/utils/profiling/profile/utils';

import {CallTreeNode} from '../callTreeNode';
import type {Frame} from '../frame';

import {Profile} from './profile';

export class ContinuousProfile extends Profile {
  static FromChunk(
    chunk: Profiling.SentryContinousProfileChunk,
    frameIndex: ReturnType<typeof createFrameIndex>
  ): Profile {
    if (chunk.profile.samples.length <= 1) {
      return Profile.Empty;
    }

    const firstSample = chunk.profile.samples[0];
    const lastSample = chunk.profile.samples[chunk.profile.samples.length - 1];

    const duration = lastSample.timestamp - firstSample.timestamp;
    const {threadId, threadName} = getThreadData(chunk);

    const profile = new ContinuousProfile({
      duration,
      endedAt: lastSample.timestamp,
      startedAt: firstSample.timestamp,
      threadId: threadId,
      name: threadName,
      type: 'flamechart',
      unit: 'milliseconds',
    });

    function resolveFrame(index) {
      const resolvedFrame = frameIndex[index];
      if (!resolvedFrame) {
        throw new Error(`Could not resolve frame ${index} in frame index`);
      }
      return resolvedFrame;
    }

    let frame: Frame | null = null;
    const resolvedStack: Frame[] = new Array(256); // stack size limit

    for (let i = 0; i < chunk.profile.samples.length; i++) {
      const sample = chunk.profile.samples[i];
      const previousSampleTimestamp =
        chunk.profile.samples[i - 1]?.timestamp ?? firstSample.timestamp;

      const stack = chunk.profile.stacks[sample.stack_id];
      let size = 0;

      for (let j = 0; j < stack.length; j++) {
        frame = resolveFrame(stack[j]);
        if (frame) resolvedStack[size++] = frame;
      }

      profile.appendSample(
        resolvedStack,
        (sample.timestamp - previousSampleTimestamp) * 1e3,
        size
      );
    }

    return profile.build();
  }

  appendSample(stack: Frame[], duration: number, end: number): void {
    // Ignore samples with 0 weight
    if (duration === 0) {
      return;
    }

    let node = this.callTree;
    const framesInStack: CallTreeNode[] = [];
    for (let i = 0; i < end; i++) {
      const frame = stack[i];
      const last = node.children[node.children.length - 1];
      // Find common frame between two stacks
      if (last && !last.isLocked() && last.frame === frame) {
        node = last;
      } else {
        const parent = node;
        node = new CallTreeNode(frame, node);
        parent.children.push(node);
      }

      node.totalWeight += duration;

      // TODO: This is On^2, because we iterate over all frames in the stack to check if our
      // frame is a recursive frame. We could do this in O(1) by keeping a map of frames in the stack
      // We check the stack in a top-down order to find the first recursive frame.
      let start = framesInStack.length - 1;
      while (start >= 0) {
        if (framesInStack[start].frame === node.frame) {
          // The recursion edge is bidirectional
          framesInStack[start].recursive = node;
          node.recursive = framesInStack[start];
          break;
        }
        start--;
      }

      framesInStack[i] = node;
    }

    node.selfWeight += duration;
    this.minFrameDuration = Math.min(duration, this.minFrameDuration);

    // Lock the stack node, so we make sure we dont mutate it in the future.
    // The samples should be ordered by timestamp when processed so we should never
    // iterate over them again in the future.
    for (const child of node.children) {
      child.lock();
    }

    node.frame.selfWeight += duration;

    for (const stackNode of framesInStack) {
      stackNode.frame.totalWeight += duration;
      stackNode.count++;
    }

    // If node is the same as the previous sample, add the weight to the previous sample
    if (node === this.samples[this.samples.length - 1]) {
      this.weights[this.weights.length - 1] += duration;
    } else {
      this.samples.push(node);
      this.weights.push(duration);
    }
  }

  // @TODO implement this when we need to extend time ranges and append new profiles
  appendProfileStart(): ContinuousProfile {
    throw new Error('Not implemented');
  }
  // @TODO implement this when we need to extend time ranges and append new profiles
  appendToProfileEnd(): ContinuousProfile {
    throw new Error('Not implemented');
  }

  build(): ContinuousProfile {
    this.duration = Math.max(
      this.duration,
      this.weights.reduce((a, b) => a + b, 0)
    );

    // We had no frames with duration > 0, so set min duration to timeline duration
    // which effectively disables any zooming on the flamegraphs
    if (
      this.minFrameDuration === Number.POSITIVE_INFINITY ||
      this.minFrameDuration === 0
    ) {
      this.minFrameDuration = this.duration;
    }

    return this;
  }
}

const COCOA_MAIN_THREAD = 'com.apple.main-thread';
function getThreadData(profile: Profiling.SentryContinousProfileChunk): {
  threadId: number;
  threadName: string;
} {
  const {samples, queue_metadata = {}, thread_metadata = {}} = profile.profile;
  const sample = samples[0];
  const threadId = parseInt(sample.thread_id, 10);
  const threadName = thread_metadata?.[threadId]?.name;

  if (threadName) {
    return {threadId, threadName};
  }

  // cocoa has a queue address that we fall back to to try to get a thread name
  // is this the only platform string to check for?
  if (profile.platform === 'cocoa') {
    const queueName =
      sample.queue_address && queue_metadata?.[sample.queue_address]?.label;

    // if a queue has the main thread name, we discard it
    if (queueName && queueName !== COCOA_MAIN_THREAD) {
      return {threadId, threadName: queueName};
    }
  }

  return {threadId, threadName: ''};
}
