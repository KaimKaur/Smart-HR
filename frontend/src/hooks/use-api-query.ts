"use client";

import {
  useMutation,
  type UseMutationOptions,
  useQuery,
  type UseQueryOptions,
} from "@tanstack/react-query";

export function useApiQuery<TData, TError = Error>(
  options: UseQueryOptions<TData, TError>,
) {
  return useQuery(options);
}

export function useApiMutation<TData, TVariables, TError = Error>(
  options: UseMutationOptions<TData, TError, TVariables>,
) {
  return useMutation(options);
}
