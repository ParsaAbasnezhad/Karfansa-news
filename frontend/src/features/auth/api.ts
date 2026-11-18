import { apiClient } from "@/lib/api-client";

const root = "auth/";

export interface AuthUser {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  mobile: string | null;
  email_verified: boolean;
  mobile_verified: boolean;
  date_joined: string;
}

export interface RegistrationInput {
  first_name: string;
  last_name: string;
  email?: string;
  mobile?: string;
  password: string;
  password_confirmation: string;
  verification_method: "email" | "sms";
}

export interface ChallengeResponse {
  message: string;
  challenge_id: string;
}

export const authApi = {
  me: () => apiClient.get<{ user: AuthUser }>(`${root}me/`),
  updateProfile: (input: { first_name: string; last_name: string }) =>
    apiClient.patch<{ user: AuthUser }>(`${root}me/`, input),
  register: (input: RegistrationInput) =>
    apiClient.post<ChallengeResponse>(`${root}register/`, input),
  verifyRegistration: (challenge_id: string, code: string) =>
    apiClient.post<{ user: AuthUser }>(`${root}verify-registration/`, { challenge_id, code }),
  login: (identifier: string, password: string) =>
    apiClient.post<{ user: AuthUser }>(`${root}login/`, { identifier, password }),
  requestLoginOtp: (identifier: string) =>
    apiClient.post<ChallengeResponse>(`${root}request-login-otp/`, { identifier }),
  verifyLoginOtp: (challenge_id: string, code: string) =>
    apiClient.post<{ user: AuthUser }>(`${root}verify-login-otp/`, { challenge_id, code }),
  resendOtp: (challenge_id: string) =>
    apiClient.post<ChallengeResponse>(`${root}resend-otp/`, { challenge_id }),
  forgotPassword: (identifier: string) =>
    apiClient.post<ChallengeResponse>(`${root}forgot-password/`, { identifier }),
  verifyResetOtp: (challenge_id: string, code: string) =>
    apiClient.post<{ reset_token: string }>(`${root}verify-reset-otp/`, { challenge_id, code }),
  resetPassword: (reset_token: string, new_password: string, password_confirmation: string) =>
    apiClient.post<{ message: string }>(`${root}reset-password/`, {
      reset_token,
      new_password,
      password_confirmation,
    }),
  requestChangePasswordOtp: () =>
    apiClient.post<ChallengeResponse>(`${root}request-change-password-otp/`, {}),
  changePassword: (
    challenge_id: string,
    code: string,
    new_password: string,
    password_confirmation: string,
  ) =>
    apiClient.post<{ message: string }>(`${root}change-password/`, {
      challenge_id,
      code,
      new_password,
      password_confirmation,
    }),
  requestContactVerification: (method: "email" | "sms") =>
    apiClient.post<ChallengeResponse>(`${root}request-contact-verification/`, { method }),
  verifyContact: (challenge_id: string, code: string) =>
    apiClient.post<{ user: AuthUser }>(`${root}verify-contact/`, { challenge_id, code }),
  logout: () => apiClient.post<{ message: string }>(`${root}logout/`, {}),
};
